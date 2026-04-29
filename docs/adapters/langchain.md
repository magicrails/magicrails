# LangChain adapter

!!! info "Coming in v0.2"
    Native LangChain / LangGraph adapters land in v0.2 (planned for late June 2026). Track progress at [issue tracker](https://github.com/magicrails/magicrails/issues).

## Workaround for v0.1

Until the v0.2 adapter ships, you can wire Magicrails into LangChain by recording tokens from a callback handler:

```python
from langchain.callbacks.base import BaseCallbackHandler
from magicrails import current

class MagicrailsHandler(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs):
        session = current()
        if session is None:
            return
        usage = response.llm_output.get("token_usage", {})
        model = response.llm_output.get("model_name")
        if model and usage:
            session.record_tokens(
                model=model,
                input=usage.get("prompt_tokens", 0),
                output=usage.get("completion_tokens", 0),
            )
```

Use it:

```python
from langchain_openai import ChatOpenAI
from magicrails import Magicrails

llm = ChatOpenAI(model="gpt-4o", callbacks=[MagicrailsHandler()])

with Magicrails(budget_usd=10.0):
    llm.invoke("hi")  # auto-counted via the callback
```

## Status

| Framework | Native adapter | Workaround |
|---|---|---|
| LangChain (legacy chains) | v0.2 | Callback handler above |
| LangGraph | v0.2 | Same callback handler ([invocation differs](https://langchain-ai.github.io/langgraph/)) |
| LangSmith integration | v0.3 | n/a |

If you're blocking on this, comment on the v0.2 milestone issue and we'll prioritise.
