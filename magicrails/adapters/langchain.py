"""Auto-instrument LangChain / LangGraph runnables to report to Magicrails.

Both LangChain and LangGraph share LangChain's callback system, so a single
`BaseCallbackHandler` subclass is enough to cover both frameworks.

Usage:

    from magicrails import Magicrails
    from magicrails.adapters.langchain import MagicrailsCallbackHandler

    callback = MagicrailsCallbackHandler()
    with Magicrails(budget_usd=10.0, max_repeats=3):
        app.invoke(state, config={"callbacks": [callback]})

`langchain-core` is the only required dependency — Magicrails itself does
not pull it in. If the user imports this module without langchain-core
installed, instantiation raises a clear ImportError.
"""
from __future__ import annotations

from typing import Any, Optional

from .._session import current

try:
    from langchain_core.callbacks import BaseCallbackHandler  # type: ignore[import-not-found]

    _LANGCHAIN_AVAILABLE = True
except ImportError:
    BaseCallbackHandler = object  # type: ignore[assignment,misc]
    _LANGCHAIN_AVAILABLE = False


_INSTALL_HINT = (
    "magicrails.adapters.langchain requires langchain-core. "
    "Install with: pip install langchain-core"
)


class MagicrailsCallbackHandler(BaseCallbackHandler):  # type: ignore[misc,valid-type]
    """LangChain/LangGraph callback that pipes events to the active Magicrails session.

    - `on_llm_end` extracts token usage from the LLMResult and feeds BudgetCeiling.
    - `on_tool_start` reports each tool invocation to RepeatCallGuard.

    Events fired outside an active Magicrails session are silently dropped, so
    it's safe to attach the callback unconditionally and only enable Magicrails
    in some code paths.
    """

    def __init__(self) -> None:
        if not _LANGCHAIN_AVAILABLE:
            raise ImportError(_INSTALL_HINT)
        super().__init__()

    # ------------------------------------------------------------------
    # token accounting
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        session = current()
        if session is None:
            return
        usage = _extract_token_usage(response)
        if usage is None:
            return
        model, input_tokens, output_tokens = usage
        session.record_tokens(model=model, input=input_tokens, output=output_tokens)

    # ------------------------------------------------------------------
    # tool-call tracking
    def on_tool_start(
        self,
        serialized: Optional[dict[str, Any]],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        session = current()
        if session is None:
            return
        name = (serialized or {}).get("name") or "unknown_tool"
        # input_str is LangChain's serialized input (often a JSON string).
        # We pass it as-is so RepeatCallGuard's hash sees identical inputs as identical.
        session.record_call(name, {"input": input_str})


# ----------------------------------------------------------------------
# extraction helpers — kept private and conservative.
#
# LangChain's token-usage shape varies by provider and version. We try the
# most-common locations in priority order and return the first match.

def _extract_token_usage(response: Any) -> Optional[tuple[str, int, int]]:
    """Return (model, input_tokens, output_tokens) or None.

    Sources tried, in order:
      1. response.llm_output["token_usage"]               (legacy LangChain)
      2. AIMessage.usage_metadata on the first generation (modern LangChain)
      3. response.llm_output["model_name"] for model id   (legacy)
      4. response.generations[0][0].message.response_metadata["model_name"]
    """
    model = _extract_model_name(response)
    input_tokens, output_tokens = 0, 0

    llm_output = getattr(response, "llm_output", None) or {}
    token_usage = llm_output.get("token_usage") if isinstance(llm_output, dict) else None
    if isinstance(token_usage, dict):
        # OpenAI-style keys
        input_tokens = int(
            token_usage.get("prompt_tokens", 0)
            or token_usage.get("input_tokens", 0)
        )
        output_tokens = int(
            token_usage.get("completion_tokens", 0)
            or token_usage.get("output_tokens", 0)
        )

    if input_tokens == 0 and output_tokens == 0:
        # Modern path: AIMessage.usage_metadata on the first generation
        meta = _first_generation_usage_metadata(response)
        if meta:
            input_tokens = int(meta.get("input_tokens", 0))
            output_tokens = int(meta.get("output_tokens", 0))

    if input_tokens == 0 and output_tokens == 0:
        return None
    return model, input_tokens, output_tokens


def _extract_model_name(response: Any) -> str:
    llm_output = getattr(response, "llm_output", None) or {}
    if isinstance(llm_output, dict):
        name = llm_output.get("model_name") or llm_output.get("model")
        if isinstance(name, str) and name:
            return name
    # Walk into generations[0][0].message.response_metadata
    try:
        gen = response.generations[0][0]
        meta = getattr(gen.message, "response_metadata", None) or {}
        name = meta.get("model_name") or meta.get("model")
        if isinstance(name, str) and name:
            return name
    except (AttributeError, IndexError, TypeError):
        pass
    return "unknown"


def _first_generation_usage_metadata(response: Any) -> Optional[dict[str, Any]]:
    try:
        gen = response.generations[0][0]
        meta = getattr(gen.message, "usage_metadata", None)
        if isinstance(meta, dict):
            return meta
    except (AttributeError, IndexError, TypeError):
        pass
    return None
