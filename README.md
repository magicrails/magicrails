<p align="center">
  <img src="https://raw.githubusercontent.com/magicrails/magicrails/main/assets/logo.png" alt="MagicRails — the meerkat that halts your runaway AI agent" width="180" />
</p>

<h1 align="center">MagicRails</h1>

<p align="center"><em>An emergency brake for AI agents.</em></p>

<p align="center">
  <a href="https://github.com/magicrails/magicrails/actions/workflows/ci.yml"><img src="https://github.com/magicrails/magicrails/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/magicrails/"><img src="https://img.shields.io/pypi/v/magicrails.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/magicrails/"><img src="https://img.shields.io/pypi/pyversions/magicrails.svg" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

<p align="center">
  <a href="https://asciinema.org/a/GLF1cEzA3apRlRtF">
    <img src="https://asciinema.org/a/GLF1cEzA3apRlRtF.svg" alt="Magicrails halting a runaway agent before the bill arrives" width="720" />
  </a>
</p>

> ⚠️ **Alpha (v0.1).** API may change before v1.0. Not yet recommended for production.

Budget caps, loop detection, and state-stasis guards — in three lines of code.

```python
from magicrails import guard

@guard(budget_usd=10.0, max_repeats=3, stasis_steps=5)
def my_agent(task): ...
```

That's it. If your agent loops, stalls, or runs past its budget, Magicrails halts it before you get the bill.

### What it looks like

```
🤖 Customer Support Agent — Task #4729
task   : refund a duplicate charge for customer #1124
model  : claude-opus-4-7
budget : $5.00   (Magicrails 🛑 watching)

step   1  thinking…                              [█░░░░░░░░░░░░░░░░░░░░░░░] $ 0.23
step   6  calling search_orders(customer=1124)   [██████░░░░░░░░░░░░░░░░░░] $ 1.35
step  12  calling search_orders(customer=1124)   [████████████░░░░░░░░░░░░] $ 2.70
step  18  calling search_orders(customer=1124)   [███████████████████░░░░░] $ 4.05
step  23  thinking…                              [████████████████████████] $ 5.17

🛑  HALT  🛑
[BudgetCeiling] Budget ceiling $5.00 reached (spent $5.1750)

halted in : ~3.4s
left running overnight at this cost-per-step, the bill would be ~$648.

✓ saved by Magicrails
```

Run it yourself: `python examples/runaway_agent.py`.

---

## Why

Every agent developer has either had — or is one bug away from — a $500 overnight invoice from a runaway agent. The agent retries the same tool forever, the cost graph goes vertical, and you find out at breakfast.

Observability tools show you the disaster. **Magicrails stops it.**

## Install

```bash
pip install magicrails
```

Zero required dependencies. Pure Python. Python 3.10+.

## The three guards

### 1. Budget ceiling — a hard dollar cap

Tokens are counted, priced against a community-maintained table, and summed per session. When the session crosses the limit, the agent is halted.

```python
from magicrails import Magicrails

with Magicrails(budget_usd=10.0) as session:
    resp = client.messages.create(model="claude-opus-4-7", messages=[...])
    session.record_tokens(
        model="claude-opus-4-7",
        input=resp.usage.input_tokens,
        output=resp.usage.output_tokens,
    )
```

Or use an adapter and let Magicrails instrument your client automatically — no manual `record_tokens` calls:

```python
from anthropic import Anthropic
from magicrails import Magicrails
from magicrails.adapters import anthropic as magicrails_anthropic

client = magicrails_anthropic.instrument(Anthropic())

with Magicrails(budget_usd=10.0):
    client.messages.create(model="claude-opus-4-7", messages=[...])  # auto-counted
```

Same shape for OpenAI:

```python
from openai import OpenAI
from magicrails import Magicrails
from magicrails.adapters import openai as magicrails_openai

client = magicrails_openai.instrument(OpenAI())

with Magicrails(budget_usd=10.0):
    client.chat.completions.create(model="gpt-4o", messages=[...])  # auto-counted
```

### 2. Repeat-call guard — stop tool loops dead

If the agent calls the same tool with the same arguments N times, it's probably stuck. Magicrails halts it.

```python
with Magicrails(max_repeats=3) as session:
    session.record_call("list_files", {"path": "/tmp"})  # ok
    session.record_call("list_files", {"path": "/tmp"})  # ok
    session.record_call("list_files", {"path": "/tmp"})  # 🛑 TripError
```

### 3. State-stasis guard — catch reasoning loops

Hash the agent's state after each step. If it hasn't moved in K steps, the agent is thinking in circles.

```python
with Magicrails(stasis_steps=5) as session:
    for step in agent.run():
        session.record_state(agent.state)
```

## On-trip actions

By default, a trip raises `magicrails.TripError`. You can override:

```python
from magicrails import guard, actions

# Ask a human in the terminal
@guard(budget_usd=10.0, on_trip=actions.prompt_human)
def my_agent(task): ...

# Send to Slack / PagerDuty / anywhere
@guard(budget_usd=10.0, on_trip=actions.webhook("https://hooks.slack.com/..."))
def my_agent(task): ...

# Custom handler
def alert(reason):
    logger.critical(f"Agent tripped: {reason}")

@guard(budget_usd=10.0, on_trip=alert)
def my_agent(task): ...
```

## Framework adapters

| Framework       | Import                         | Status      |
| --------------- | ------------------------------ | ----------- |
| OpenAI SDK      | `magicrails.adapters.openai`        | ✅ v0.1     |
| Anthropic SDK   | `magicrails.adapters.anthropic`     | ✅ v0.1     |
| LangChain       | `magicrails.adapters.langchain`     | ✅ v0.1.2   |
| LangGraph       | `magicrails.adapters.langgraph`     | ✅ v0.1.2   |
| CrewAI          | `magicrails.adapters.crewai`        | 🚧 v0.2     |
| AutoGen         | `magicrails.adapters.autogen`       | 🚧 v0.2     |
| OpenTelemetry   | `magicrails.adapters.otel`          | 🚧 v0.2     |

Adapters are one-file. PRs welcome.

## Pricing table

[`magicrails/models.json`](magicrails/models.json) ships with reasonable defaults for the major current models (per 1M tokens, USD). Override or extend:

```python
my_pricing = {
    "my-internal-model": {"input": 0.10, "output": 0.30},
}
with Magicrails(budget_usd=5.0, pricing=my_pricing) as session:
    ...
```

Unknown models are counted as $0 and emit a `WARNING` on the `magicrails` logger (once per model per process). Add the model to your pricing dict to enforce a real budget.

## Philosophy

Magicrails is **not** an observability platform. It is **not** a tracing tool. It does **one thing**: stop an agent that is about to cost you money or time you cannot get back.

- **Three lines of code.** Anything more is too much friction.
- **In-process.** No server, no daemon, no cloud account.
- **Zero required deps.** Drop it into any project.
- **Framework agnostic.** Adapters, not lock-in.

If you want traces, use [Langfuse](https://langfuse.com) or [Arize Phoenix](https://phoenix.arize.com). If you want routing, use [LiteLLM](https://github.com/BerriAI/litellm). Magicrails composes with those; it doesn't replace them.

## Examples

- [examples/runaway_agent.py](examples/runaway_agent.py) — **the headline demo.** Watch a stuck support agent burn through a $5 budget in ~3 seconds before Magicrails halts it. Projects what the bill *would* have been left running overnight.
- [examples/basic.py](examples/basic.py) — minimal integration
- [examples/budget_demo.py](examples/budget_demo.py) — bare-bones token loop
- [examples/repeat_loop_demo.py](examples/repeat_loop_demo.py) — catch a stuck tool loop

Run the headline demo:

```bash
pip install -e .
python examples/runaway_agent.py
```

Want to share it? Record an asciinema cast and convert to GIF:

```bash
asciinema rec -c "python examples/runaway_agent.py" save.cast
agg save.cast save.gif --speed 1.0 --theme monokai
```

## Roadmap

- **v0.1** — three detectors, OpenAI & Anthropic adapters *(you are here)*
- **v0.2** — LangChain / LangGraph / CrewAI adapters, OpenTelemetry span processor, per-tool sub-budgets
- **v0.3** — adaptive thresholds, multi-session dashboards
- **v1.0** — optional local dashboard (Tauri) for live sessions, Slack/Discord control surface

## Contributing

PRs for adapters, pricing updates, and new detectors are very welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide — including the recipe for adding a new framework adapter.

Quick start:

```bash
pip install -e '.[dev]'
pytest
ruff check magicrails tests
```

## License

MIT. See [LICENSE](LICENSE).

---

**Save your agent from itself. `pip install magicrails`.**
