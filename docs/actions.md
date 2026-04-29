# On-trip actions

By default, when a guard trips, Magicrails raises `magicrails.TripError`. You can override that behaviour for any session.

## Built-in actions

### Default — raise `TripError`

```python
from magicrails import Magicrails

with Magicrails(budget_usd=10.0):
    ...  # TripError on overrun
```

The exception carries a `TripReason` with the detector name, the threshold, and the value that crossed it.

### `prompt_human` — ask a human in the terminal

```python
from magicrails import guard, actions

@guard(budget_usd=10.0, on_trip=actions.prompt_human)
def my_agent(task): ...
```

When the budget trips, the agent halts and the prompt asks (on stderr): "halt? continue? raise?". Useful for interactive long-running scripts where you'd rather decide live than restart.

### `webhook(url)` — send to Slack / PagerDuty / anywhere

```python
from magicrails import guard, actions

@guard(
    budget_usd=10.0,
    on_trip=actions.webhook("https://hooks.slack.com/..."),
)
def my_agent(task): ...
```

Posts a JSON payload like:

```json
{
  "detector": "BudgetCeiling",
  "message": "Budget ceiling $10.00 reached (spent $10.10)",
  "value": 10.10,
  "threshold": 10.00,
  "session_id": "abc123"
}
```

The HTTP call uses the standard library only (no `requests` dependency). Failures in the webhook itself are logged and the original `TripError` is still raised.

## Custom handler

Any callable taking a `TripReason` works:

```python
import logging
from magicrails import guard

logger = logging.getLogger("my_app")

def alert(reason):
    logger.critical("Agent tripped: %s", reason)

@guard(budget_usd=10.0, on_trip=alert)
def my_agent(task): ...
```

If your handler returns `None`, the session still raises `TripError` after the handler runs (so your code's `try/except` still works as expected). If your handler raises, that exception propagates instead.

## Combining handlers

Magicrails ships small primitives — chain them yourself:

```python
from magicrails import guard, actions

slack = actions.webhook("https://hooks.slack.com/...")

def alert_then_prompt(reason):
    slack(reason)
    actions.prompt_human(reason)

@guard(budget_usd=10.0, on_trip=alert_then_prompt)
def my_agent(task): ...
```

## Webhook payload schema

Stable for v0.1.x. May add fields in v0.2 (never remove).

| Field | Type | Description |
|---|---|---|
| `detector` | str | Name of the detector that fired (e.g., `BudgetCeiling`) |
| `message` | str | Human-readable explanation |
| `value` | float \| int \| str | The value that crossed the threshold |
| `threshold` | float \| int | The configured limit |
| `session_id` | str | Unique session identifier |
