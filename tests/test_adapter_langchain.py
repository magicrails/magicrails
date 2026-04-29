"""Tests for the LangChain/LangGraph callback adapter.

The tests deliberately don't depend on `langchain-core` being installed.
They exercise the pure extraction helpers with duck-typed mocks and bypass
__init__ on the handler class to test its callback methods in isolation.
A separate, skipped-if-absent test verifies the ImportError contract.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from magicrails import Magicrails, TripError
from magicrails.adapters import langchain as adapter
from magicrails.adapters.langchain import (
    MagicrailsCallbackHandler,
    _extract_model_name,
    _extract_token_usage,
)

# ---------------------------------------------------------------------------
# extraction helpers — pure functions, no langchain dep needed.

class TestExtractTokenUsage:
    def test_legacy_openai_shape(self):
        resp = SimpleNamespace(
            llm_output={
                "token_usage": {"prompt_tokens": 100, "completion_tokens": 50},
                "model_name": "gpt-4o",
            },
            generations=[],
        )
        assert _extract_token_usage(resp) == ("gpt-4o", 100, 50)

    def test_legacy_anthropic_shape(self):
        resp = SimpleNamespace(
            llm_output={
                "token_usage": {"input_tokens": 200, "output_tokens": 80},
                "model_name": "claude-opus-4-7",
            },
            generations=[],
        )
        assert _extract_token_usage(resp) == ("claude-opus-4-7", 200, 80)

    def test_modern_usage_metadata(self):
        message = SimpleNamespace(
            usage_metadata={"input_tokens": 300, "output_tokens": 120},
            response_metadata={"model_name": "claude-sonnet-4-6"},
        )
        gen = SimpleNamespace(message=message)
        resp = SimpleNamespace(llm_output={}, generations=[[gen]])
        assert _extract_token_usage(resp) == ("claude-sonnet-4-6", 300, 120)

    def test_returns_none_when_no_usage(self):
        resp = SimpleNamespace(llm_output={}, generations=[])
        assert _extract_token_usage(resp) is None

    def test_returns_none_when_zero_tokens(self):
        # Zero tokens on both sides → treat as "no real usage" rather than
        # spamming the session with $0 events.
        resp = SimpleNamespace(
            llm_output={"token_usage": {"prompt_tokens": 0, "completion_tokens": 0}},
            generations=[],
        )
        assert _extract_token_usage(resp) is None

    def test_falls_back_to_unknown_model(self):
        resp = SimpleNamespace(
            llm_output={"token_usage": {"prompt_tokens": 10, "completion_tokens": 5}},
            generations=[],
        )
        assert _extract_token_usage(resp) == ("unknown", 10, 5)


class TestExtractModelName:
    def test_from_llm_output_model_name(self):
        resp = SimpleNamespace(llm_output={"model_name": "gpt-5"}, generations=[])
        assert _extract_model_name(resp) == "gpt-5"

    def test_from_llm_output_model(self):
        resp = SimpleNamespace(llm_output={"model": "claude-haiku-4-5"}, generations=[])
        assert _extract_model_name(resp) == "claude-haiku-4-5"

    def test_from_generation_metadata(self):
        message = SimpleNamespace(response_metadata={"model_name": "claude-opus-4-7"})
        gen = SimpleNamespace(message=message)
        resp = SimpleNamespace(llm_output={}, generations=[[gen]])
        assert _extract_model_name(resp) == "claude-opus-4-7"

    def test_unknown_when_missing(self):
        resp = SimpleNamespace(llm_output={}, generations=[])
        assert _extract_model_name(resp) == "unknown"


# ---------------------------------------------------------------------------
# handler routing — bypass __init__ so we don't need langchain installed.

def _make_handler() -> MagicrailsCallbackHandler:
    """Return a handler instance without calling __init__ (which would need langchain)."""
    return MagicrailsCallbackHandler.__new__(MagicrailsCallbackHandler)


class TestHandlerRouting:
    def test_on_llm_end_records_tokens_in_session(self):
        handler = _make_handler()
        with Magicrails(budget_usd=100.0) as session:
            resp = SimpleNamespace(
                llm_output={
                    "token_usage": {"prompt_tokens": 1000, "completion_tokens": 500},
                    "model_name": "gpt-4o",
                },
                generations=[],
            )
            handler.on_llm_end(resp)
            # gpt-4o: $2.50/1M in, $10/1M out → $0.0025 + $0.005 = $0.0075
            assert session.spent_usd == pytest.approx(0.0075, rel=1e-6)

    def test_on_llm_end_outside_session_is_silent(self):
        handler = _make_handler()
        # No active session — must not raise.
        resp = SimpleNamespace(
            llm_output={"token_usage": {"prompt_tokens": 100, "completion_tokens": 50}},
            generations=[],
        )
        # No assertion needed — absence of an exception is the test.
        handler.on_llm_end(resp)

    def test_on_llm_end_with_no_usage_is_silent(self):
        handler = _make_handler()
        with Magicrails(budget_usd=100.0) as session:
            resp = SimpleNamespace(llm_output={}, generations=[])
            handler.on_llm_end(resp)
            assert session.spent_usd == 0.0

    def test_on_tool_start_records_call(self):
        handler = _make_handler()
        with Magicrails(max_repeats=3) as session:
            handler.on_tool_start({"name": "search_orders"}, '{"customer": 1124}')
            handler.on_tool_start({"name": "search_orders"}, '{"customer": 1124}')
            assert session.tripped is None
            with pytest.raises(TripError):
                # Third call with identical args trips RepeatCallGuard,
                # which raises via the default on_trip handler.
                handler.on_tool_start({"name": "search_orders"}, '{"customer": 1124}')
            assert session.tripped is not None
            assert session.tripped.detector == "RepeatCallGuard"

    def test_on_tool_start_unnamed_tool_falls_back(self):
        """Missing or empty `serialized` should not crash the handler."""
        handler = _make_handler()
        # max_repeats high enough that the test exercises the name-fallback
        # path without tripping the guard.
        with Magicrails(max_repeats=10):
            handler.on_tool_start(None, "input")
            handler.on_tool_start({}, "different input")

    def test_on_tool_start_outside_session_is_silent(self):
        handler = _make_handler()
        handler.on_tool_start({"name": "x"}, "input")  # no session active


# ---------------------------------------------------------------------------
# import-error contract

def test_instantiation_without_langchain_raises():
    """When langchain-core is not installed, instantiating the handler must
    raise a clear ImportError pointing at the install command."""
    if adapter._LANGCHAIN_AVAILABLE:
        pytest.skip("langchain-core is installed; ImportError path not testable")
    with pytest.raises(ImportError, match="langchain-core"):
        MagicrailsCallbackHandler()


def test_langgraph_module_reexports_handler():
    """The langgraph adapter is a thin re-export of the langchain handler."""
    from magicrails.adapters.langchain import MagicrailsCallbackHandler as LC
    from magicrails.adapters.langgraph import MagicrailsCallbackHandler as LG

    assert LC is LG
