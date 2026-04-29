# Getting started

Five minutes from `pip install` to a halted agent.

## 1. Install

```bash
pip install magicrails
```

That's it. Zero dependencies. Python 3.10+.

## 2. The decorator

The shortest path to a guarded agent:

```python
from magicrails import guard

@guard(budget_usd=10.0, max_repeats=3, stasis_steps=5)
def my_agent(task: str) -> str:
    # your existing agent loop
    ...
```

Three thresholds wired in one line. If any one trips, the agent halts.

## 3. Watch it halt

Save this as `demo.py`:

```python
from magicrails import Magicrails

with Magicrails(max_repeats=3) as session:
    session.record_call("list_files", {"path": "/tmp"})  # ok
    session.record_call("list_files", {"path": "/tmp"})  # ok
    session.record_call("list_files", {"path": "/tmp"})  # raises TripError
```

Run it:

```bash
python demo.py
```

You'll see:

```
magicrails.exceptions.TripError: [RepeatCallGuard] Tool 'list_files' called 3 times with identical arguments
```

That's the contract. Three identical calls, halt. No budget needed, no LLM needed — Magicrails works on any agent loop you can wrap in a context manager.

## 4. The context manager vs. the decorator

Both expose the same three guards. Pick whichever fits your agent shape:

=== "Decorator"

    ```python
    from magicrails import guard

    @guard(budget_usd=10.0, max_repeats=3)
    def my_agent(task):
        ...
    ```

=== "Context manager"

    ```python
    from magicrails import Magicrails

    with Magicrails(budget_usd=10.0, max_repeats=3) as session:
        run_agent(session)
    ```

Inside the wrapped function or block, the *current* session is reachable via `magicrails.current()` — useful for libraries that want to record tokens or tool calls without taking the session as an argument.

## 5. Plug in real LLM calls

Manual recording works:

```python
with Magicrails(budget_usd=10.0) as session:
    resp = client.messages.create(model="claude-opus-4-7", messages=[...])
    session.record_tokens(
        model="claude-opus-4-7",
        input=resp.usage.input_tokens,
        output=resp.usage.output_tokens,
    )
```

Or use an [adapter](adapters/anthropic.md) and let Magicrails instrument the SDK for you — no manual `record_tokens` calls.

## Where to go next

- **[Budget ceiling](guards/budget.md)** — how cost is estimated, sub-budgets, custom pricing tables.
- **[Repeat-call guard](guards/repeat.md)** — window size, fingerprinting, false-positive avoidance.
- **[State-stasis guard](guards/stasis.md)** — the `state_projector` pattern for filtering timestamps and UUIDs.
- **[On-trip actions](actions.md)** — webhooks, Slack, custom halt logic.
