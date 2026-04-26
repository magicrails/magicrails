"""Magicrails — an emergency brake for AI agents."""
from __future__ import annotations

from ._session import Magicrails, current
from .guard import guard
from .events import TripReason, ToolCall, TokenUsage
from .exceptions import TripError
from . import actions

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
