# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-04-27

Initial public release.

### Added

- `Magicrails` context manager and `@guard` decorator for halting AI agents on detected failure modes.
- Three detectors:
  - `BudgetCeiling` — halts the session when cumulative estimated token cost crosses a USD threshold.
  - `RepeatCallGuard` — halts the session when the same tool is invoked with identical arguments past a configurable threshold within a sliding window.
  - `StateStasis` — halts the session when the hash of the agent state remains unchanged across consecutive observations.
- On-trip actions: `default_halt`, `prompt_human`, and `webhook(url)`.
- SDK adapters in `magicrails.adapters`:
  - OpenAI Python SDK (auto-instruments `client.chat.completions.create`).
  - Anthropic Python SDK (auto-instruments `client.messages.create`).
- Pricing table in `magicrails/models.json` covering current OpenAI, Anthropic, Google, and DeepSeek models (per 1M tokens, USD). Verified against Anthropic's pricing docs and the LiteLLM community pricing registry on 2026-04-26. The table records its verification date in a `_meta` block; underscore-prefixed keys are reserved for metadata and ignored by `estimate_cost`.
- Examples: `examples/basic.py`, `examples/budget_demo.py`, `examples/repeat_loop_demo.py`.
- Tests for all detectors, the session lifecycle, and the pricing layer.

### Notes

- Public API is intentionally minimal: `Magicrails`, `current`, `guard`, `TripReason`, `ToolCall`, `TokenUsage`, `TripError`, `actions`.
- Zero required runtime dependencies. Python 3.10+.
- Unknown models are currently counted as $0 with a `WARNING` on the `magicrails` logger. A `pricing_mode="strict"` option that fails closed is roadmapped for v0.2.
