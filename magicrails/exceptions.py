from __future__ import annotations

from .events import TripReason


class TripError(RuntimeError):
    """Raised when a Magicrails guard trips."""

    def __init__(self, reason: TripReason):
        super().__init__(str(reason))
        self.reason = reason
