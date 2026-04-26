from __future__ import annotations

import functools
from typing import Any, Callable, Optional, TypeVar

from ._session import Magicrails
from .events import TripReason

F = TypeVar("F", bound=Callable[..., Any])


def guard(
    budget_usd: Optional[float] = None,
    max_repeats: Optional[int] = None,
    stasis_steps: Optional[int] = None,
    on_trip: Optional[Callable[[TripReason], None]] = None,
    pricing: Optional[dict] = None,
    repeat_window: int = 32,
) -> Callable[[F], F]:
    """Decorator form of `Magicrails`. Wrap any agent-running function."""

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with Magicrails(
                budget_usd=budget_usd,
                max_repeats=max_repeats,
                stasis_steps=stasis_steps,
                on_trip=on_trip,
                pricing=pricing,
                repeat_window=repeat_window,
            ):
                return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
