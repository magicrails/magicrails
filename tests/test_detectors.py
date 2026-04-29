from __future__ import annotations

import pytest

from magicrails import Magicrails, TripError
from magicrails.detectors import BudgetCeiling, RepeatCallGuard, StateStasis
from magicrails.events import TokenUsage, ToolCall


def test_repeat_call_guard_trips_on_identical_calls():
    g = RepeatCallGuard(max_repeats=3)
    assert g.observe_call(ToolCall("ls", {"path": "/tmp"})) is None
    assert g.observe_call(ToolCall("ls", {"path": "/tmp"})) is None
    reason = g.observe_call(ToolCall("ls", {"path": "/tmp"}))
    assert reason is not None
    assert reason.detector == "RepeatCallGuard"
    assert reason.details["count"] >= 3


def test_repeat_call_guard_does_not_trip_on_different_args():
    g = RepeatCallGuard(max_repeats=3)
    for i in range(10):
        assert g.observe_call(ToolCall("ls", {"path": f"/tmp/{i}"})) is None


def test_repeat_call_guard_does_not_trip_on_different_tools():
    g = RepeatCallGuard(max_repeats=3)
    for name in ["ls", "cat", "grep"]:
        assert g.observe_call(ToolCall(name, {"arg": 1})) is None


def test_budget_ceiling_trips_on_overspend():
    pricing = {"test": {"input": 10.0, "output": 20.0}}
    g = BudgetCeiling(limit_usd=1.0, pricing=pricing)
    # 50k input + 50k output → $0.50 + $1.00 = $1.50
    reason = g.observe_tokens(TokenUsage("test", 50_000, 50_000))
    assert reason is not None
    assert reason.details["spent_usd"] >= 1.0


def test_budget_ceiling_does_not_trip_under_budget():
    pricing = {"test": {"input": 10.0, "output": 20.0}}
    g = BudgetCeiling(limit_usd=100.0, pricing=pricing)
    assert g.observe_tokens(TokenUsage("test", 1000, 1000)) is None
    assert g.spent_usd > 0


def test_budget_ceiling_unknown_model_is_free():
    g = BudgetCeiling(limit_usd=1.0, pricing={})
    assert g.observe_tokens(TokenUsage("never-heard-of-it", 1_000_000, 1_000_000)) is None
    assert g.spent_usd == 0.0


def test_state_stasis_trips_on_repeat():
    g = StateStasis(max_steps=3)
    state = {"step": 1, "thought": "same"}
    assert g.observe_state(state) is None
    assert g.observe_state(state) is None
    reason = g.observe_state(state)
    assert reason is not None
    assert reason.detector == "StateStasis"


def test_state_stasis_resets_on_change():
    g = StateStasis(max_steps=3)
    g.observe_state({"a": 1})
    g.observe_state({"a": 1})
    # A different state resets the counter
    g.observe_state({"a": 2})
    # After the reset, one more identical observation must not trip
    assert g.observe_state({"a": 2}) is None


def test_full_session_raises_on_budget():
    with pytest.raises(TripError):
        with Magicrails(budget_usd=0.01) as s:
            s.record_tokens("gpt-4o", 1_000_000, 1_000_000)


def test_full_session_raises_on_repeat():
    with pytest.raises(TripError):
        with Magicrails(max_repeats=3) as s:
            for _ in range(5):
                s.record_call("ls", {"p": "/tmp"})


def test_full_session_raises_on_stasis():
    with pytest.raises(TripError):
        with Magicrails(stasis_steps=3) as s:
            for _ in range(5):
                s.record_state({"stuck": True})


def test_empty_session_is_noop():
    with Magicrails(budget_usd=1.0, max_repeats=3, stasis_steps=3):
        pass


def test_spent_usd_reflects_recorded_tokens():
    with Magicrails(budget_usd=1000.0) as s:
        s.record_tokens("gpt-4o-mini", 10_000, 10_000)
        assert s.spent_usd > 0


def test_repeat_guard_validates_args():
    with pytest.raises(ValueError):
        RepeatCallGuard(max_repeats=1)


def test_budget_ceiling_validates_args():
    with pytest.raises(ValueError):
        BudgetCeiling(limit_usd=0)


def test_state_stasis_validates_args():
    with pytest.raises(ValueError):
        StateStasis(max_steps=1)


# --- state_projector --------------------------------------------------------


def test_state_projector_filters_volatile_fields_so_stasis_trips():
    """Without a projector the timestamp would change every step and stasis
    would never trip. With a projector that drops the timestamp, identical
    'real' state trips at max_steps."""
    project = lambda s: {k: v for k, v in s.items() if k != "timestamp"}
    g = StateStasis(max_steps=3, state_projector=project)

    assert g.observe_state({"plan": "do X", "timestamp": 1_700_000_000}) is None
    assert g.observe_state({"plan": "do X", "timestamp": 1_700_000_001}) is None
    reason = g.observe_state({"plan": "do X", "timestamp": 1_700_000_002})

    assert reason is not None
    assert reason.detector == "StateStasis"


def test_state_projector_still_detects_real_change():
    """A projector should not mask real state progress."""
    project = lambda s: {k: v for k, v in s.items() if k != "timestamp"}
    g = StateStasis(max_steps=3, state_projector=project)

    g.observe_state({"plan": "step 1", "timestamp": 1_700_000_000})
    g.observe_state({"plan": "step 2", "timestamp": 1_700_000_001})
    # Two different projected states → counter never reaches 3 even with
    # one more identical-to-the-last observation.
    assert g.observe_state({"plan": "step 2", "timestamp": 1_700_000_002}) is None


def test_state_projector_threads_through_session():
    """Magicrails(state_projector=...) plumbs to the StateStasis detector."""
    project = lambda s: {k: v for k, v in s.items() if k != "ts"}
    with Magicrails(stasis_steps=3, state_projector=project) as s:
        s.record_state({"plan": "x", "ts": 1})
        s.record_state({"plan": "x", "ts": 2})
        with pytest.raises(TripError):
            s.record_state({"plan": "x", "ts": 3})


# --- volatile-field heuristic warning ---------------------------------------


def test_warns_on_unix_timestamp_field_value(caplog):
    """A bare numeric field whose value is in the UNIX-timestamp range."""
    with caplog.at_level("WARNING", logger="magicrails"):
        g = StateStasis(max_steps=3)
        # Field name 'epoch' avoids the name-based shortcut so the value check fires.
        g.observe_state({"step": 1, "epoch": 1_710_000_000.5})
    msgs = [r.getMessage() for r in caplog.records]
    assert any("UNIX timestamp" in m for m in msgs), msgs


def test_warns_on_iso8601_string(caplog):
    with caplog.at_level("WARNING", logger="magicrails"):
        g = StateStasis(max_steps=3)
        g.observe_state({"created": "2026-04-27T10:30:00Z", "step": 1})
    msgs = [r.getMessage() for r in caplog.records]
    # Either the field-name match ("created") or the value match should fire.
    assert any("created" in m for m in msgs), msgs


def test_warns_on_uuid_value(caplog):
    with caplog.at_level("WARNING", logger="magicrails"):
        g = StateStasis(max_steps=3)
        g.observe_state({"request_id": "550e8400-e29b-41d4-a716-446655440000"})
    msgs = [r.getMessage() for r in caplog.records]
    assert any("UUID" in m for m in msgs), msgs


def test_warns_on_field_named_timestamp(caplog):
    with caplog.at_level("WARNING", logger="magicrails"):
        g = StateStasis(max_steps=3)
        g.observe_state({"plan": "x", "timestamp": 0})  # name-based, not value-based
    msgs = [r.getMessage() for r in caplog.records]
    assert any("timestamp" in m.lower() for m in msgs), msgs


def test_warning_does_not_fire_when_projector_is_set(caplog):
    """A configured projector means the user has acknowledged the issue."""
    with caplog.at_level("WARNING", logger="magicrails"):
        g = StateStasis(max_steps=3, state_projector=lambda s: s)
        g.observe_state({"timestamp": 1_700_000_000})
    assert caplog.records == []


def test_warning_fires_only_once_per_detector(caplog):
    with caplog.at_level("WARNING", logger="magicrails"):
        g = StateStasis(max_steps=3)
        g.observe_state({"timestamp": 1_700_000_000})
        g.observe_state({"timestamp": 1_700_000_001})
        g.observe_state({"timestamp": 1_700_000_002})
    assert len(caplog.records) == 1


def test_no_warning_for_clean_state(caplog):
    """A simple state with no volatile fields should not warn."""
    with caplog.at_level("WARNING", logger="magicrails"):
        g = StateStasis(max_steps=3)
        g.observe_state({"plan": "step 1", "step_number": 1, "thought": "hello"})
    assert caplog.records == []


def test_step_counter_is_not_flagged_as_timestamp(caplog):
    """An integer step counter must not look like a UNIX timestamp."""
    with caplog.at_level("WARNING", logger="magicrails"):
        g = StateStasis(max_steps=3)
        g.observe_state({"step": 42, "iteration": 17, "depth": 1})
    assert caplog.records == []


def test_bool_field_is_not_flagged_as_timestamp(caplog):
    """Bool subclasses int but must not be treated as a timestamp."""
    with caplog.at_level("WARNING", logger="magicrails"):
        g = StateStasis(max_steps=3)
        g.observe_state({"done": True, "active": False})
    assert caplog.records == []
