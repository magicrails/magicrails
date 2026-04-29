from __future__ import annotations

import contextvars
from typing import Any, Callable, Optional

from .actions import default_halt
from .detectors import BudgetCeiling, Detector, RepeatCallGuard, StateStasis
from .events import TokenUsage, ToolCall, TripReason

_current: contextvars.ContextVar[Optional["Magicrails"]] = contextvars.ContextVar(
    "magicrails_current", default=None
)


def current() -> Optional["Magicrails"]:
    """Return the Magicrails session active in this context, or None."""
    return _current.get()


class Magicrails:
    """Context manager that watches an agent's activity and halts it on trip."""

    def __init__(
        self,
        budget_usd: Optional[float] = None,
        max_repeats: Optional[int] = None,
        stasis_steps: Optional[int] = None,
        state_projector: Optional[Callable[[Any], Any]] = None,
        on_trip: Optional[Callable[[TripReason], None]] = None,
        pricing: Optional[dict] = None,
        detectors: Optional[list[Detector]] = None,
        repeat_window: int = 32,
    ):
        self.detectors: list[Detector] = list(detectors or [])
        if budget_usd is not None:
            self.detectors.append(BudgetCeiling(limit_usd=budget_usd, pricing=pricing))
        if max_repeats is not None:
            self.detectors.append(
                RepeatCallGuard(max_repeats=max_repeats, window=repeat_window)
            )
        if stasis_steps is not None:
            self.detectors.append(
                StateStasis(max_steps=stasis_steps, state_projector=state_projector)
            )
        self.on_trip = on_trip or default_halt
        self._token: Optional[contextvars.Token] = None
        self._tripped: Optional[TripReason] = None

    def __enter__(self) -> "Magicrails":
        self._token = _current.set(self)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self._token is not None:
            _current.reset(self._token)
            self._token = None
        return False

    @property
    def tripped(self) -> Optional[TripReason]:
        return self._tripped

    @property
    def spent_usd(self) -> float:
        for d in self.detectors:
            if isinstance(d, BudgetCeiling):
                return d.spent_usd
        return 0.0

    def record_call(self, name: str, args: Optional[dict[str, Any]] = None) -> None:
        event = ToolCall(name=name, args=args or {})
        for d in self.detectors:
            reason = d.observe_call(event)
            if reason is not None:
                self._trip(reason)

    def record_tokens(self, model: str, input: int, output: int) -> None:
        event = TokenUsage(model=model, input_tokens=input, output_tokens=output)
        for d in self.detectors:
            reason = d.observe_tokens(event)
            if reason is not None:
                self._trip(reason)

    def record_state(self, state: Any) -> None:
        for d in self.detectors:
            reason = d.observe_state(state)
            if reason is not None:
                self._trip(reason)

    def _trip(self, reason: TripReason) -> None:
        if self._tripped is not None:
            return
        self._tripped = reason
        self.on_trip(reason)
