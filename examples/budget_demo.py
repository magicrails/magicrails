"""Budget demo — the headline feature.

Simulates an agent burning tokens in a loop. Magicrails stops it at $10.

Run:
    python examples/budget_demo.py
"""
from __future__ import annotations

from magicrails import Magicrails, TripError


def main() -> None:
    step = 0
    with Magicrails(budget_usd=10.0) as session:
        try:
            for step in range(1000):
                session.record_tokens(
                    model="claude-opus-4-7",
                    input=5_000,
                    output=3_000,
                )
                print(f"step {step:3d} | spent ${session.spent_usd:.4f}")
        except TripError as e:
            print(f"\n🛑 Magicrails halted the agent at step {step}: {e.reason}")
            print(f"Total spent: ${session.spent_usd:.4f}")


if __name__ == "__main__":
    main()
