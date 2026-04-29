# Pricing table

The pricing table is the trust contract. If users get hit with a bill that exceeds the configured ceiling, the brand dies in one tweet.

## Where it lives

[`magicrails/models.json`](https://github.com/magicrails/magicrails/blob/main/magicrails/models.json) — a flat JSON file with model IDs as keys and per-1M-token rates as values:

```json
{
  "_meta": {
    "verified": "2026-04-27",
    "unit": "USD per 1,000,000 tokens"
  },
  "claude-opus-4-7": {"input": 5.00, "output": 25.00},
  "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
  "gpt-4o": {"input": 2.50, "output": 10.00}
}
```

The `_meta` block records the verification date and source URLs. **Underscore-prefixed keys are reserved for metadata and ignored by pricing lookups.**

## How lookup works

1. Exact match: `pricing.get(model)`
2. Fallback: longest-prefix match against keys in the table (so `gpt-4o-2024-08-06` falls back to `gpt-4o`)
3. Underscore-prefixed keys are skipped at both steps
4. Unknown models: counted as `$0`, with a `WARNING` on the `magicrails` logger (once per model per process)

## Override per session

Pass a `pricing` dict to `Magicrails(...)`. Your dict is merged on top of the defaults — keys you supply override, keys you don't keep working.

```python
from magicrails import Magicrails

custom = {
    "my-internal-model": {"input": 0.10, "output": 0.30},
    "claude-opus-4-7": {"input": 4.00, "output": 20.00},  # negotiated rate
}

with Magicrails(budget_usd=5.0, pricing=custom) as session:
    ...
```

## Contributing pricing updates

Provider rates change. Pricing PRs are the highest-leverage contribution we accept.

1. Check provider docs for the new rate
2. Update `magicrails/models.json`
3. Bump the `_meta.verified` date
4. Add a line to `CHANGELOG.md`
5. Open the PR with the provider doc URL in the description

We aim to merge pricing PRs within 24h. Consider this the fastest path to your name in the contributors list.

## Sources

The bundled table is verified against:

- [Anthropic pricing docs](https://docs.anthropic.com/en/docs/about-claude/pricing)
- [OpenAI pricing](https://openai.com/api/pricing/)
- [Google Gemini pricing](https://ai.google.dev/pricing)
- [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing)
- [LiteLLM community price registry](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json)

## What's not modeled (yet)

- **Prompt caching discounts** — current behaviour treats all input tokens at the standard rate. You'll halt slightly earlier than the real bill (conservative).
- **Batch API discounts** — same; conservative over-count.
- **Data residency / fast-mode multipliers** — not yet modelled. If you're on one of these tiers, override `pricing` per session.
- **Reasoning-token classes** (e.g., extended thinking) — rolled into the standard input/output counts.

Tracking issue for these: see the v0.2 milestone.
