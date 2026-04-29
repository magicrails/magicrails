"""Magicrails callback for LangGraph.

LangGraph builds on LangChain's runnable + callback system, so the same
`MagicrailsCallbackHandler` works for both. This module re-exports it
under the `langgraph` adapter namespace for discoverability.

Usage:

    from magicrails import Magicrails
    from magicrails.adapters.langgraph import MagicrailsCallbackHandler

    callback = MagicrailsCallbackHandler()
    with Magicrails(budget_usd=10.0, max_repeats=3):
        graph.invoke(state, config={"callbacks": [callback]})
"""
from __future__ import annotations

from .langchain import MagicrailsCallbackHandler

__all__ = ["MagicrailsCallbackHandler"]
