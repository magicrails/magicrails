# OpenAI adapter

Drop-in instrumentation for the official `openai` Python SDK. Auto-records token usage from `client.chat.completions.create` so you don't have to call `record_tokens` manually.

## Install

The OpenAI SDK is not a Magicrails dependency — install it yourself if you don't have it.

```bash
pip install openai magicrails
```

## Use

```python
from openai import OpenAI
from magicrails import Magicrails
from magicrails.adapters import openai as magicrails_openai

client = magicrails_openai.instrument(OpenAI())

with Magicrails(budget_usd=10.0):
    client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "hi"}],
    )
    # token usage was automatically recorded against the active session
```

That's the whole integration. The instrumented client is a drop-in replacement.

## What it does

- Wraps `client.chat.completions.create`
- Extracts `response.usage.prompt_tokens` and `response.usage.completion_tokens`
- Calls `magicrails.current().record_tokens(model, input, output)` if a session is active
- No-op when no session is active — safe to call from anywhere

## What it doesn't do (yet)

- Streaming responses — partial-token accounting on the way in v0.2
- The `responses` API (newer endpoint) — open an issue if you need it
- Embeddings / moderations — these don't usually pose budget risk; not instrumented by default

## Multiple sessions / nested

If you nest `Magicrails(...)` blocks (e.g., a per-agent session inside a per-task session), the adapter records to the **innermost** active session. This is usually what you want.

## Errors raised by the LLM

The adapter does not interfere with errors. If `chat.completions.create` raises, your code sees the raise as it normally would.
