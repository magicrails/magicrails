from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger("magicrails")

_DEFAULT: Optional[dict] = None
_DEFAULT_LOCK = threading.Lock()
_WARNED_MODELS: set[str] = set()
_WARNED_LOCK = threading.Lock()


def load_default_pricing() -> dict:
    global _DEFAULT
    if _DEFAULT is None:
        with _DEFAULT_LOCK:
            if _DEFAULT is None:
                path = Path(__file__).with_name("models.json")
                with path.open() as f:
                    _DEFAULT = json.load(f)
    return _DEFAULT


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    pricing: dict,
) -> float:
    # Underscore-prefixed keys (e.g. "_meta") are reserved for metadata.
    rates = None if model.startswith("_") else pricing.get(model)
    if rates is None:
        candidates = [k for k in pricing if not k.startswith("_")]
        for key in sorted(candidates, key=len, reverse=True):
            if model.startswith(key):
                rates = pricing[key]
                break
    if rates is None:
        _warn_unknown_model(model)
        return 0.0
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


def _warn_unknown_model(model: str) -> None:
    # Warn once per process per model — repeated calls would spam logs.
    with _WARNED_LOCK:
        if model in _WARNED_MODELS:
            return
        _WARNED_MODELS.add(model)
    logger.warning(
        "magicrails: model %r not in pricing table; counting as $0. "
        "Add it to your pricing dict to enforce a real budget.",
        model,
    )
