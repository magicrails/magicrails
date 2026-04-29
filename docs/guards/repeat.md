# Repeat-call guard

If the agent calls the same tool with the same arguments N times, it's probably stuck in a loop. The repeat-call guard halts the session when that happens.

## How it works

Every time you (or an adapter) call `session.record_call(tool, args)`, Magicrails computes a fingerprint of `(tool, args)` and checks how many times that fingerprint has appeared in the recent window. If the count meets `max_repeats`, the session trips.

## Basic usage

```python
from magicrails import Magicrails

with Magicrails(max_repeats=3) as session:
    session.record_call("list_files", {"path": "/tmp"})  # 1
    session.record_call("list_files", {"path": "/tmp"})  # 2
    session.record_call("list_files", {"path": "/tmp"})  # 3 — TripError
```

A different argument resets the streak for that fingerprint:

```python
with Magicrails(max_repeats=3) as session:
    session.record_call("list_files", {"path": "/tmp"})    # 1
    session.record_call("list_files", {"path": "/tmp"})    # 2
    session.record_call("list_files", {"path": "/home"})   # 1 — different args, fresh
    session.record_call("list_files", {"path": "/tmp"})    # 3 — TripError on /tmp
```

## Argument fingerprinting

Arguments are JSON-serialized and hashed. Order-independent: `{"a": 1, "b": 2}` and `{"b": 2, "a": 1}` collapse to the same fingerprint.

This means:

- Calls to `list_files({"path": "/tmp"})` and `list_files({"path": "/tmp"})` collide ✅
- Calls with floating-point timestamps embedded in args do not collide (each timestamp is unique)
- Calls where one extra optional field flips do not collide

If your tool accepts noisy args (timestamps, request IDs, retry counts), filter them before recording — the agent is "really" calling the same tool if you, the developer, would consider the calls equivalent.

## Sliding window

The default window is per-session (the entire session counts). To detect *recent* loops only, you can lower the window so distant calls don't count toward the streak.

```python
# (window-size config — exact API check the source for v0.1; v0.2 makes this a first-class param)
```

## False positives — when to lower or raise the threshold

| Scenario | Symptom | Fix |
|---|---|---|
| Polling a status endpoint | Trips on legitimate retries | Raise `max_repeats`, or filter the polling tool from `record_call` |
| Idempotent reads | Trips on a read-only tool that's expected to be called many times | Raise `max_repeats`, or wrap that tool's call site in a `with Magicrails(max_repeats=None)` block |
| Real loop | Trips correctly, agent stops | This is the goal |

A reasonable starting threshold is **3** for unfamiliar agents and **5–10** for agents with known polling/retry patterns. Tune from there.

## Recording from an adapter

Adapters record calls automatically when they wrap framework-level tool invocations. See **[Adapters](../adapters/openai.md)**.
