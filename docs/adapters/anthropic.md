# Anthropic adapter

Drop-in instrumentation for the official `anthropic` Python SDK. Auto-records token usage from `client.messages.create` so you don't have to call `record_tokens` manually.

## Install

The Anthropic SDK is not a Magicrails dependency — install it yourself if you don't have it.

```bash
pip install anthropic magicrails
```

## Use

```python
from anthropic import Anthropic
from magicrails import Magicrails
from magicrails.adapters import anthropic as magicrails_anthropic

client = magicrails_anthropic.instrument(Anthropic())

with Magicrails(budget_usd=10.0):
    client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        messages=[{"role": "user", "content": "hi"}],
    )
    # token usage was automatically recorded against the active session
```

That's the whole integration.

## What it does

- Wraps `client.messages.create`
- Extracts `response.usage.input_tokens` and `response.usage.output_tokens`
- Calls `magicrails.current().record_tokens(model, input, output)` if a session is active
- No-op when no session is active

## What it doesn't do (yet)

- Streaming responses — partial-token accounting on the way in v0.2
- Cache discount accounting — current behaviour over-counts cached input tokens (you'll halt slightly earlier than the real bill, never later)
- Vision / extended thinking token classes — these are rolled into the standard input/output counts; per-class accounting is roadmapped for v0.2

## Multiple sessions / nested

If you nest `Magicrails(...)` blocks, the adapter records to the **innermost** active session.

## Errors raised by the LLM

The adapter does not interfere with errors. If `messages.create` raises, your code sees the raise as it normally would.
