"""Repeat-call demo.

Simulates an agent stuck retrying the same tool forever.

Run:
    python examples/repeat_loop_demo.py
"""
from __future__ import annotations

from magicrails import Magicrails, TripError


def main() -> None:
    with Magicrails(max_repeats=3) as session:
        try:
            for i in range(100):
                session.record_call("search_docs", {"query": "how to fix bug"})
                print(f"iteration {i}: agent called search_docs again...")
        except TripError as e:
            print(f"\n🛑 {e.reason}")


if __name__ == "__main__":
    main()
