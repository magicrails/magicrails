"""Minimal Magicrails example.

Run:
    python examples/basic.py
"""
from __future__ import annotations

from magicrails import Magicrails, TripError


def list_files(path: str) -> list[str]:
    return ["a.txt", "b.txt"]


def main() -> None:
    with Magicrails(max_repeats=3) as session:
        try:
            for _ in range(100):
                session.record_call("list_files", {"path": "/tmp"})
                list_files("/tmp")
        except TripError as e:
            print(f"Agent halted: {e.reason}")


if __name__ == "__main__":
    main()
