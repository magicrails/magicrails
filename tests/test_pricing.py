from __future__ import annotations

from magicrails.pricing import estimate_cost, load_default_pricing


def test_default_pricing_loads():
    p = load_default_pricing()
    assert "gpt-4o" in p
    assert "claude-opus-4-7" in p


def test_exact_match():
    pricing = {"foo": {"input": 1.0, "output": 2.0}}
    # 1M input @ $1/M = $1, 1M output @ $2/M = $2, total $3
    assert estimate_cost("foo", 1_000_000, 1_000_000, pricing) == 3.0


def test_prefix_match():
    pricing = {"gpt-4o": {"input": 2.5, "output": 10.0}}
    cost = estimate_cost("gpt-4o-2024-08-06", 1_000_000, 0, pricing)
    assert cost == 2.5


def test_longest_prefix_wins():
    pricing = {
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4o": {"input": 2.5, "output": 10.0},
    }
    # Should match gpt-4o, not gpt-4
    assert estimate_cost("gpt-4o-mini-preview", 1_000_000, 0, pricing) == 2.5


def test_unknown_model_zero():
    assert estimate_cost("ghost-model", 10_000, 10_000, {}) == 0.0
