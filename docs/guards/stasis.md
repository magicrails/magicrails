# State-stasis guard

If the agent's "state" hasn't changed in K consecutive observations, it's thinking in circles — even if its tool calls vary. The state-stasis guard catches this reasoning-loop class of failure.

## How it works

After each agent step, you call `session.record_state(state)`. Magicrails hashes the state and compares it to the previous hash. If the hash is unchanged for `stasis_steps` consecutive observations, the session trips.

## Basic usage

```python
from magicrails import Magicrails

with Magicrails(stasis_steps=5) as session:
    for step in agent.run():
        session.record_state(agent.state)
```

After 5 steps where `agent.state` hashes to the same value, you get:

```
magicrails.exceptions.TripError: [StateStasis] State unchanged for 5 consecutive steps
```

## What is "state"?

Anything hashable. The most useful definition is the working memory of the agent:

- The current plan / scratchpad
- Outstanding tool calls
- Partial outputs

If the agent has produced no new tokens, no new plan items, no new tool results in 5 steps, it's stuck.

## The `state_projector` parameter

State often contains noise that changes every step but doesn't represent real progress:

- Wall-clock timestamps
- UUIDs / request IDs
- Heartbeat counters
- The number of seconds since session start

If the noise is in the state hash, stasis will *never* trip — even on a real loop. Filter noise out before hashing by passing a `state_projector` callable (added in v0.1.1):

```python
def project(state: dict) -> dict:
    return {k: v for k, v in state.items() if k not in ("timestamp", "request_id")}

with Magicrails(stasis_steps=5, state_projector=project) as session:
    ...
```

The projector is applied before hashing. A good projector is the smallest function that returns "the part of the state that changes when real work happens."

!!! tip "Built-in heuristic warning (v0.1.1+)"
    On the first observed state, if no `state_projector` is set and Magicrails detects a UNIX timestamp, ISO-8601 datetime string, UUID, or a field named `timestamp` / `created` / `updated` / `*_at`, you'll get a one-shot `WARNING` on the `magicrails` logger pointing you at `state_projector`. The warning fires at most once per detector instance and goes away as soon as you pass a projector.

!!! warning "Stasis false positives are the most common Magicrails failure mode"
    If stasis trips on agents that are working correctly, the cause is almost always: your state contains a wall-clock timestamp, UUID, or counter that mutates every step regardless of progress. Add a `state_projector` to filter it out.

## Choosing `stasis_steps`

| Threshold | When |
|---|---|
| 3 | Tight agents that should make visible progress every step |
| 5 (default) | Mixed-workload agents — fast tools and reasoning steps interleaved |
| 10+ | Long-thinking agents (multi-step planning, deep reasoning) where some steps legitimately produce no state change |

Higher thresholds = lower false-positive rate, slower detection of real loops. Tune to your agent.

## When stasis is the wrong guard

- **Agent state isn't well-defined** — for fully external agents (e.g., browser-use agents whose "state" is a screenshot), you'd need a vision-aware projector. Defer.
- **Streaming output** — if the agent's only "state change" is the LLM streaming tokens, stasis trips when the stream stalls. That might be what you want; or you might prefer a `max_seconds_per_step` guard (roadmapped for v0.2).
