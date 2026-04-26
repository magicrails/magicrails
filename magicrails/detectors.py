from __future__ import annotations

import hashlib
import json
from collections import deque
from typing import Any, Optional

from .events import TokenUsage, ToolCall, TripReason
from .pricing import estimate_cost, load_default_pricing


class Detector:
    """Subclass and override whichever observe_* hooks apply."""

    def observe_call(self, event: ToolCall) -> Optional[TripReason]:
        return None

    def observe_tokens(self, event: TokenUsage) -> Optional[TripReason]:
        return None

    def observe_state(self, state: Any) -> Optional[TripReason]:
        return None


class RepeatCallGuard(Detector):
    """Trip when the same (tool, args) appears `max_repeats` times in a window."""

    def __init__(self, max_repeats: int, window: int = 32):
        if max_repeats < 2:
            raise ValueError("max_repeats must be >= 2")
        self.max_repeats = max_repeats
        self.window = window
        self.recent: deque = deque(maxlen=window)

    def observe_call(self, event: ToolCall) -> Optional[TripReason]:
        fingerprint = (event.name, _stable_hash(event.args))
        self.recent.append(fingerprint)
        count = sum(1 for fp in self.recent if fp == fingerprint)
        if count >= self.max_repeats:
            return TripReason(
                detector="RepeatCallGuard",
                message=(
                    f"Tool {event.name!r} called {count} times "
                    f"with identical arguments"
                ),
                details={
                    "tool": event.name,
                    "args": event.args,
                    "count": count,
                },
            )
        return None


class BudgetCeiling(Detector):
    """Trip when cumulative estimated cost crosses `limit_usd`."""

    def __init__(self, limit_usd: float, pricing: Optional[dict] = None):
        if limit_usd <= 0:
            raise ValueError("limit_usd must be > 0")
        self.limit_usd = limit_usd
        self.pricing = pricing or load_default_pricing()
        self.spent_usd: float = 0.0

    def observe_tokens(self, event: TokenUsage) -> Optional[TripReason]:
        cost = estimate_cost(
            event.model,
            event.input_tokens,
            event.output_tokens,
            self.pricing,
        )
        self.spent_usd += cost
        if self.spent_usd >= self.limit_usd:
            return TripReason(
                detector="BudgetCeiling",
                message=(
                    f"Budget ceiling ${self.limit_usd:.2f} reached "
                    f"(spent ${self.spent_usd:.4f})"
                ),
                details={
                    "limit_usd": self.limit_usd,
                    "spent_usd": self.spent_usd,
                    "last_model": event.model,
                    "last_input_tokens": event.input_tokens,
                    "last_output_tokens": event.output_tokens,
                },
            )
        return None


class StateStasis(Detector):
    """Trip when agent state hash does not change across `max_steps` consecutive observations."""

    def __init__(self, max_steps: int):
        if max_steps < 2:
            raise ValueError("max_steps must be >= 2")
        self.max_steps = max_steps
        self.last_hash: Optional[str] = None
        # Counts total consecutive observations of the same state (not repeats).
        # E.g. max_steps=3 means: observe the same state 3 times in a row → trip.
        self.same_count = 0

    def observe_state(self, state: Any) -> Optional[TripReason]:
        h = _stable_hash(state)
        if h == self.last_hash:
            self.same_count += 1
        else:
            self.same_count = 1
            self.last_hash = h
        if self.same_count >= self.max_steps:
            return TripReason(
                detector="StateStasis",
                message=f"Agent state unchanged for {self.same_count} iterations",
                details={
                    "steps": self.same_count,
                    "state_hash": h,
                },
            )
        return None


def _stable_hash(obj: Any) -> str:
    try:
        payload = json.dumps(obj, sort_keys=True, default=str).encode()
    except TypeError:
        payload = repr(obj).encode()
    return hashlib.sha256(payload).hexdigest()
