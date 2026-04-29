# FAQ

## Why "Magicrails"?

Magic = the agent does its thing. Rails = it stays on the track. The library is the rails.

## How does this compare to Langfuse / Arize Phoenix / Helicone?

Those are **observability** platforms — they show you what your agent did. Magicrails is a **guardrail** — it stops your agent before the disaster.

You'd use both: Langfuse for traces and analytics; Magicrails to halt the runaway. They compose cleanly because Magicrails is in-process and emits no telemetry of its own.

## How does this compare to LangChain's `max_iterations`?

`max_iterations` caps the number of agent steps. That's useful but coarse:

- It can't tell the difference between 10 productive steps and 10 looping ones.
- It doesn't catch budget overruns at all — a single expensive prompt can blow the bill.
- It's framework-specific.

Magicrails' three guards (budget, repeat-call, state-stasis) are framework-agnostic and address different failure modes. Use both — they're complementary.

## Does this work with my framework?

Native adapters in v0.1: OpenAI SDK, Anthropic SDK. v0.2 (planned late June 2026): LangChain, LangGraph, CrewAI, AutoGen, OpenTelemetry.

For unsupported frameworks: any place you can call `session.record_tokens(...)` or `session.record_call(...)` works. The library is a context manager and three method calls.

## I hit a false positive — agent halted but it was making progress

The most common cause is the **state-stasis guard** when your state contains a wall-clock timestamp, UUID, or counter that changes every step regardless of progress. See **[State-stasis guard](guards/stasis.md#the-state_projector-pattern)** for the `state_projector` pattern.

Second most common: **repeat-call guard** with a polling tool. Either raise the threshold or filter that tool from `record_call`.

If you've ruled both out and it's still tripping incorrectly, please [open an issue](https://github.com/magicrails/magicrails/issues) with a minimal repro.

## Why no dependencies?

Three reasons:

1. **Trust.** A guardrails library that pulls in 30 transitive deps has 30 attack surfaces. Yours doesn't.
2. **Drop-in.** No version conflicts with whatever LLM SDK / framework you're already using.
3. **Speed.** `pip install magicrails` is fast. People install it and try it the same minute they read the README.

We'll keep it this way.

## Why is the alpha banner so loud?

Because the API will change before v1.0. Pin a version (`magicrails==0.1.0`) and you're stable; track `latest` and you may need to update call sites in 0.2.

## Where do I report a security issue?

See [SECURITY.md](https://github.com/magicrails/magicrails/blob/main/SECURITY.md). Short version: email rather than open a public issue.

## Can I sponsor this project?

Yes — [GitHub Sponsors](https://github.com/sponsors/magicrails) (when enabled). Sponsorship money pays for the maintainer's time on bug-fix releases and adapter rot maintenance. There is no paid tier, no hosted product, and no plan to add either in v1.x.

## I want to contribute — what do you need?

Highest leverage in v0.1: **adapter PRs** (LangChain, LangGraph, CrewAI, AutoGen, Pydantic-AI) and **pricing-table updates** when providers change rates. See [CONTRIBUTING.md](https://github.com/magicrails/magicrails/blob/main/CONTRIBUTING.md).
