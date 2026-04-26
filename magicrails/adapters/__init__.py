"""Framework adapters.

Each adapter exposes an `instrument(client)` function that wraps the client's
LLM entry point so that token usage is reported to the active Magicrails session
automatically.
"""
