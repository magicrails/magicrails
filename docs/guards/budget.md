# Budget ceiling

A hard dollar cap on the cumulative token cost of a session. The single most important guard for protecting yourself from a runaway agent.

## How it works

1. Every time you (or an adapter) call `session.record_tokens(model, input, output)`, Magicrails looks up the model in the pricing table.
2. The token count is multiplied by the per-million-token rates and added to the running total.
3. If the running total `>= budget_usd`, the session trips with `TripReason("BudgetCeiling", ...)`.

The pricing table ships with current rates for major Anthropic, OpenAI, Google, and DeepSeek models. See **[Pricing table](../pricing.md)** for the full list and the verification date.

## Basic usage

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

Or use an adapter to skip the manual `record_tokens` call entirely — see **[Adapters](../adapters/openai.md)**.

## Custom pricing

Override or extend the default table:

```python
my_pricing = {
    "my-internal-model": {"input": 0.10, "output": 0.30},  # USD per 1M tokens
}
with Magicrails(budget_usd=5.0, pricing=my_pricing) as session:
    ...
```

Magicrails merges your dict on top of the defaults — keys you provide override, keys you don't keep working.

## Unknown models

If a model isn't in the pricing table, the cost is counted as `$0` and a `WARNING` is emitted on the `magicrails` logger (once per model per process).

```text
WARNING:magicrails:magicrails: model 'my-custom-model' not in pricing table; counting as $0. Add it to your pricing dict to enforce a real budget.
```

This means a typo'd model name silently disables budget enforcement for that call. Watch the logs; or wait for `pricing_mode="strict"` (roadmapped for v0.2) which fails closed.

## Prefix matching

The pricing table supports prefix matching. If you record tokens for `gpt-4o-2024-08-06`, the lookup falls back to the longest matching prefix in the table — so `gpt-4o` rates apply.

This means:

- Dated model snapshots (`gpt-4o-2024-08-06`) inherit rates from the base model
- New model variants you forgot to add still get a sensible fallback price

If you need exact-only matching, override the table with the exact ID you want.

## Common gotchas

| Gotcha | Symptom | Fix |
|---|---|---|
| Model not in table | Budget never trips, total looks suspiciously low | Add the model to your pricing dict, or check logs for the `WARNING` |
| Forgot to call `record_tokens` | Budget never trips | Use an [adapter](../adapters/openai.md) — they auto-record |
| Budget set in dollars, but you meant tokens | Budget trips immediately or never | `budget_usd` is in dollars; the table is per 1M tokens |
| Cached input tokens | Slight over-counting on prompts that hit prompt caches | Pricing table doesn't yet model cache discounts; the over-count is conservative (you'll halt earlier than the real bill) |
