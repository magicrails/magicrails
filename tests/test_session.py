from __future__ import annotations

import pytest

from magicrails import Magicrails, TripError, current, guard
from magicrails.events import TripReason


def test_current_is_none_outside_session():
    assert current() is None


def test_current_is_set_inside_session():
    with Magicrails(budget_usd=1.0) as s:
        assert current() is s


def test_current_resets_after_exit():
    with Magicrails(budget_usd=1.0):
        pass
    assert current() is None


def test_current_resets_after_exception():
    with pytest.raises(TripError):
        with Magicrails(budget_usd=0.01):
            current().record_tokens("gpt-4o", 1_000_000, 1_000_000)
    assert current() is None


def test_custom_on_trip_is_called():
    calls: list[TripReason] = []

    def handler(reason: TripReason):
        calls.append(reason)

    with Magicrails(max_repeats=3, on_trip=handler) as s:
        for _ in range(5):
            s.record_call("x", {})
    assert len(calls) == 1
    assert calls[0].detector == "RepeatCallGuard"


def test_on_trip_fires_only_once():
    calls: list[TripReason] = []

    with Magicrails(max_repeats=3, on_trip=calls.append) as s:
        for _ in range(20):
            s.record_call("x", {})
    assert len(calls) == 1


def test_guard_decorator_halts():
    @guard(budget_usd=0.01)
    def agent():
        from magicrails import current

        current().record_tokens("gpt-4o", 1_000_000, 1_000_000)

    with pytest.raises(TripError):
        agent()


def test_repeat_window_can_be_widened():
    # With default window=32, identical calls separated by >32 distinct calls
    # would be evicted. Setting repeat_window large enough keeps them.
    with pytest.raises(TripError):
        with Magicrails(max_repeats=2, repeat_window=200) as s:
            s.record_call("ls", {"p": "/tmp"})
            for i in range(100):
                s.record_call("noop", {"i": i})
            s.record_call("ls", {"p": "/tmp"})


def test_webhook_rejects_invalid_url():
    from magicrails import actions

    with pytest.raises(ValueError):
        actions.webhook("not-a-url")
    with pytest.raises(ValueError):
        actions.webhook("ftp://example.com/hook")


def test_unknown_model_emits_warning(caplog):
    import logging

    from magicrails.pricing import _WARNED_MODELS, estimate_cost

    _WARNED_MODELS.discard("brand-new-model")
    with caplog.at_level(logging.WARNING, logger="magicrails"):
        estimate_cost("brand-new-model", 1000, 1000, {})
    assert any("brand-new-model" in r.message for r in caplog.records)
