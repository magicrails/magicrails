# Contributing to Magicrails

Thanks for considering a contribution. Magicrails is intentionally small — the goal is to keep it the kind of dependency people are happy to add to their project. Read the [Philosophy](README.md#philosophy) section before opening a large PR.

## Development setup

```bash
git clone https://github.com/magicrails/magicrails
cd magicrails
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
```

## Running checks locally

```bash
pytest                          # all tests should pass
ruff check magicrails tests     # lint
python -m build                 # confirm the package still builds
```

CI runs the same three steps across Python 3.10–3.13 on Linux, plus 3.12 on macOS and Windows.

## What we welcome

- **New framework adapters** (LangChain, LangGraph, CrewAI, AutoGen, LiteLLM, OpenTelemetry...). One file under 60 lines, mirroring `magicrails/adapters/openai.py`.
- **Pricing table updates** in [`magicrails/models.json`](magicrails/models.json). Cite the vendor's pricing page in the PR description.
- **New detectors** that are stateless between sessions and have a clear "this is what trips it" rule. Subclass `Detector` and override the relevant `observe_*` hook.
- **On-trip actions** (Slack, PagerDuty, OpsGenie, etc.) added under `magicrails/actions.py`.
- **Bug fixes and tests** for any of the above.

## What we'll likely push back on

- Tracing, logging, or observability features. Magicrails composes with [Langfuse](https://langfuse.com), [Phoenix](https://phoenix.arize.com), and OpenTelemetry — it doesn't replace them.
- Required runtime dependencies. Magicrails is zero-dep on purpose. Adapters can import their target SDK lazily.
- Configuration that adds more knobs than it removes mistakes.

## Conventions

- **Type hints on all public APIs.** Internal helpers can be looser.
- **Tests live under `tests/`** and mirror the module they cover (`magicrails/foo.py` → `tests/test_foo.py`).
- **No comments unless the *why* is non-obvious.** Well-named code is the documentation.
- **Detectors are stateless across sessions.** State lives on the instance, and the instance lives for one `Magicrails(...)` block.

## Adding a framework adapter — quick recipe

1. Create `magicrails/adapters/<framework>.py` (mirror `openai.py`).
2. Wrap the SDK's "make a call" method so it forwards `(model, input_tokens, output_tokens)` to `current().record_tokens(...)` after each call.
3. Add a row to the **Framework adapters** table in `README.md` with status `✅`.
4. Add a usage snippet (3–6 lines) to `README.md` under the existing OpenAI/Anthropic examples.
5. Add at least one test using a fake client object (don't hit the real API in tests).

## Releasing (maintainers only)

1. Bump `version` in `pyproject.toml`.
2. Commit, tag `vX.Y.Z`, push the tag.
3. The `release.yml` workflow verifies the tag matches `pyproject.toml`, publishes to PyPI via OIDC trusted publishing, and creates a GitHub Release with auto-generated notes.

## Code of conduct

Be kind. Assume good faith. Disagreements about technical direction are welcome; personal attacks aren't.

## License

By contributing, you agree your contribution will be licensed under the [MIT License](LICENSE).
