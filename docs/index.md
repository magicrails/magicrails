# Magicrails

*An emergency brake for AI agents.*

Budget caps, loop detection, and state-stasis guards — in three lines of code.

```python
from magicrails import guard

@guard(budget_usd=10.0, max_repeats=3, stasis_steps=5)
def my_agent(task): ...
```

If your agent loops, stalls, or runs past its budget, Magicrails halts it before you get the bill.

## Why

Every agent developer has either had — or is one bug away from — a $500 overnight invoice from a runaway agent. The agent retries the same tool forever, the cost graph goes vertical, and you find out at breakfast.

Observability tools show you the disaster. **Magicrails stops it.**

## Install

```bash
pip install magicrails
```

Zero required dependencies. Pure Python. Python 3.10+.

## What's next

- **[Getting started](getting-started.md)** — a 5-minute tutorial that ends with a halted agent.
- **The three guards** — deep-dive on each detector ([budget](guards/budget.md), [repeat-call](guards/repeat.md), [state-stasis](guards/stasis.md)).
- **Adapters** — drop-in instrumentation for [OpenAI](adapters/openai.md) and [Anthropic](adapters/anthropic.md).
- **[On-trip actions](actions.md)** — what happens when a guard fires.
- **[Pricing table](pricing.md)** — the trust contract for budget enforcement.
- **[FAQ](faq.md)** — common gotchas, false-positive triage, comparison to neighbours.

## Philosophy

Magicrails is **not** an observability platform. It is **not** a tracing tool. It does **one thing**: stop an agent that is about to cost you money or time you cannot get back.

- **Three lines of code.** Anything more is too much friction.
- **In-process.** No server, no daemon, no cloud account.
- **Zero required deps.** Drop it into any project.
- **Framework agnostic.** Adapters, not lock-in.

If you want traces, use [Langfuse](https://langfuse.com) or [Arize Phoenix](https://phoenix.arize.com). If you want routing, use [LiteLLM](https://github.com/BerriAI/litellm). Magicrails composes with those; it doesn't replace them.

!!! warning "Alpha (v0.1)"
    The API may change before v1.0. Not yet recommended for production. Pin a version: `magicrails==0.1.0`.
