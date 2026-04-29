from __future__ import annotations

import hashlib
import json
import logging
import re
from collections import deque
from typing import Any, Callable, Optional

from .events import TokenUsage, ToolCall, TripReason
from .pricing import estimate_cost, load_default_pricing

logger = logging.getLogger("magicrails")


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
    """Trip when agent state hash does not change across `max_steps` consecutive observations.

    Pass a `state_projector` callable to filter wall-clock timestamps, UUIDs,
    or other per-step volatile fields out of the hash. Without this, a state
    that contains e.g. a timestamp will produce a fresh hash every step and
    stasis will never trip.
    """

    def __init__(
        self,
        max_steps: int,
        state_projector: Optional[Callable[[Any], Any]] = None,
    ):
        if max_steps < 2:
            raise ValueError("max_steps must be >= 2")
        self.max_steps = max_steps
        self.state_projector = state_projector
        self.last_hash: Optional[str] = None
        # Counts total consecutive observations of the same state (not repeats).
        # E.g. max_steps=3 means: observe the same state 3 times in a row → trip.
        self.same_count = 0
        self._heuristic_checked = False

    def observe_state(self, state: Any) -> Optional[TripReason]:
        if not self._heuristic_checked:
            self._heuristic_checked = True
            if self.state_projector is None:
                finding = _find_volatile_field(state)
                if finding is not None:
                    logger.warning(
                        "magicrails.StateStasis: state contains %s — stasis will "
                        "likely never trip because the hash will change every step. "
                        "Pass `state_projector=fn` to Magicrails(...) to filter such "
                        "fields, or remove `stasis_steps=` if stasis isn't useful here.",
                        finding,
                    )

        projected = self.state_projector(state) if self.state_projector else state
        h = _stable_hash(projected)
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


# --- volatile-field heuristic for StateStasis ---------------------------------
#
# False-positive prevention: the most common reason StateStasis appears broken
# in practice is that user state contains a wall-clock timestamp or a UUID that
# changes every step. The hash then changes every step, so the counter never
# advances and the guard never trips. We scan the first observed state for
# obvious offenders and warn once.

_TIMESTAMP_FIELD_NAMES = frozenset(
    {"timestamp", "ts", "time", "now", "date", "datetime", "created", "updated", "modified"}
)
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_ISO8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")


def _looks_like_unix_timestamp(value: Any) -> bool:
    # bool is a subclass of int; we want to ignore it
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    # Seconds-precision range: 2017-07-14 .. 2033-05-18
    if 1_500_000_000 <= value <= 2_000_000_000:
        return True
    # Milliseconds-precision range
    if 1_500_000_000_000 <= value <= 2_000_000_000_000:
        return True
    return False


def _looks_like_unique_string_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if _UUID_RE.match(value):
        return True
    if _ISO8601_RE.match(value):
        return True
    return False


def _find_volatile_field(state: Any, path: str = "") -> Optional[str]:
    """Return a description of the first volatile-looking field, or None.

    Recurses into dicts and lists/tuples. Stops at first hit. Bounded depth
    to avoid pathological inputs.
    """
    return _find_volatile_field_bounded(state, path, depth_left=6)


def _find_volatile_field_bounded(state: Any, path: str, depth_left: int) -> Optional[str]:
    if depth_left <= 0:
        return None
    if isinstance(state, dict):
        for k, v in state.items():
            kp = f"{path}.{k}" if path else str(k)
            kl = str(k).lower()
            if kl in _TIMESTAMP_FIELD_NAMES or kl.endswith("_at"):
                return f"key {kp!r} (looks like a timestamp by name)"
            if _looks_like_unix_timestamp(v):
                return f"key {kp!r} = {v!r} (looks like a UNIX timestamp)"
            if _looks_like_unique_string_id(v):
                return f"key {kp!r} = {v!r} (looks like a UUID or ISO datetime)"
            child = _find_volatile_field_bounded(v, kp, depth_left - 1)
            if child is not None:
                return child
        return None
    if isinstance(state, (list, tuple)):
        for i, v in enumerate(state):
            ip = f"{path}[{i}]" if path else f"[{i}]"
            if _looks_like_unix_timestamp(v):
                return f"value at {ip} = {v!r} (looks like a UNIX timestamp)"
            if _looks_like_unique_string_id(v):
                return f"value at {ip} = {v!r} (looks like a UUID or ISO datetime)"
            child = _find_volatile_field_bounded(v, ip, depth_left - 1)
            if child is not None:
                return child
        return None
    # Top-level scalar — check directly
    if path == "":
        if _looks_like_unix_timestamp(state):
            return f"top-level value {state!r} (looks like a UNIX timestamp)"
        if _looks_like_unique_string_id(state):
            return f"top-level value {state!r} (looks like a UUID or ISO datetime)"
    return None
