"""Auto-instrument the Anthropic client to report tokens to Magicrails."""
from __future__ import annotations

from typing import Any, TypeVar

from .._session import current

T = TypeVar("T")


def instrument(client: T) -> T:
    """Wrap `client.messages.create` so every call reports usage."""
    original = client.messages.create  # type: ignore[attr-defined]

    def wrapped(*args: Any, **kwargs: Any) -> Any:
        resp = original(*args, **kwargs)
        session = current()
        usage = getattr(resp, "usage", None)
        if session is not None and usage is not None:
            session.record_tokens(
                model=kwargs.get("model") or getattr(resp, "model", "unknown"),
                input=getattr(usage, "input_tokens", 0),
                output=getattr(usage, "output_tokens", 0),
            )
        return resp

    client.messages.create = wrapped  # type: ignore[attr-defined]
    return client
