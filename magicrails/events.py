from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenUsage:
    model: str
    input_tokens: int
    output_tokens: int


@dataclass
class TripReason:
    detector: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.detector}] {self.message}"
