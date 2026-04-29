# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.1] - 2026-04-27

The "no false-positive stasis trips" patch release. Ships within the v0.1 launch week to neutralise the most-likely real-world bug in the launch build before it bites.

### Added

- `state_projector` parameter on `StateStasis`, `Magicrails(...)`, and the `@guard` decorator. Pass a callable that filters volatile fields (timestamps, UUIDs, request IDs) out of the state before hashing — without it, a state that contains a wall-clock timestamp produces a fresh hash every step and stasis never trips.
- One-shot heuristic warning on the first observed state: when no `state_projector` is configured and the state contains a UNIX timestamp, an ISO-8601 datetime string, a UUID, or a field named `timestamp` / `created` / `updated` / `*_at`, `magicrails.StateStasis` logs a single `WARNING` explaining the issue and pointing at `state_projector`. Fires at most once per detector instance.
- 12 new tests covering the projector, heuristic detection of UNIX-second + millisecond timestamps, ISO-8601 strings, UUIDs, name-based field matches, the projector-configured silence path, and the once-per-detector limit.

### Notes

- The projector is the recommended way to use `stasis_steps` in any agent whose state contains per-step volatile data; the heuristic is a safety net, not a substitute.
- Bool values are explicitly excluded from the timestamp range check (Python booleans subclass `int`).
- Top-level scalar states are checked the same way as nested fields.

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
