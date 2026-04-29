"""Magicrails — an emergency brake for AI agents."""
from __future__ import annotations

from . import actions
from ._session import Magicrails, current
from .events import TokenUsage, ToolCall, TripReason
from .exceptions import TripError
from .guard import guard

__version__ = "0.1.0"

__all__ = [
    "Magicrails",
    "current",
    "guard",
    "TripReason",
    "ToolCall",
    "TokenUsage",
    "TripError",
    "actions",
]

del annotations
