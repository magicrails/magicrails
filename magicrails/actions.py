"""Built-in on-trip handlers."""
from __future__ import annotations

import logging
import sys
from typing import Callable
from urllib.parse import urlparse

from .events import TripReason
from .exceptions import TripError

logger = logging.getLogger("magicrails")


def default_halt(reason: TripReason) -> None:
    raise TripError(reason)


def prompt_human(reason: TripReason) -> None:
    print(f"\n🛑 MAGICRAILS TRIPPED: {reason}", file=sys.stderr)
    try:
        answer = input("Continue? [y/N] ").strip().lower()
    except EOFError:
        answer = ""
    if answer != "y":
        raise TripError(reason)


def webhook(url: str, also_raise: bool = True) -> Callable[[TripReason], None]:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"webhook url must be http(s) with a host, got: {url!r}")

    def _handler(reason: TripReason) -> None:
        try:
            import json
            import urllib.request

            payload = json.dumps(
                {
                    "detector": reason.detector,
                    "message": reason.message,
                    "details": reason.details,
                }
            ).encode()
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as exc:
            # webhook is best-effort; never mask the original trip, but make
            # delivery failures visible so silent alert pipelines aren't trusted.
            logger.warning("magicrails webhook to %s failed: %s", url, exc)
        if also_raise:
            raise TripError(reason)

    return _handler
