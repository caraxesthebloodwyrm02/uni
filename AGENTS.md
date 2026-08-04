# AGENTS.md

## Quick Start

```bash
unset VIRTUAL_ENV && uv sync --group dev       # install deps
unset VIRTUAL_ENV && uv run ruff check .       # lint
unset VIRTUAL_ENV && uv run ruff format .      # format
unset VIRTUAL_ENV && uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider"
```

## Environment Gotchas (host-specific, verified)

- `VIRTUAL_ENV=/home/cable/series/mangrove/venv` is exported by the shell, but uv's project env is `.venv/`. uv warns that `VIRTUAL_ENV` is ignored — `unset VIRTUAL_ENV` before any `uv`/`ruff`/`pytest` run to avoid the mismatch warning and confusion.
- Plain `uv run pytest` CRASHES on this host: the host Python lacks the `_sqlite3` module, which breaks pytest-cov's coverage plugin (addopts include `--cov`). Always use the `-o "addopts=..."` override to strip addopts (`--no-cov -p no:cacheprovider` also works).
- `.git/hooks/post-checkout` runs `scripts/attribution_oscillator.py` on every checkout, appending to the tracked `.compliance-hand-off/.audit.log` — so a clean checkout leaves modified tracked files. That's expected, not a problem. To stop it, rename `.git/hooks/post-checkout` (e.g. to `.post-checkout.disabled`).

## Project Facts

- **Python 3.13+** required (`requires-python = ">=3.13,<3.14"`)
- **Build**: hatchling, package `mangrove`, sources in `mangrove_platform/`
- **Runtime deps**: `mcp>=2.0.0,<3`, `pydantic>=2.0,<3`
- **Dev deps**: pytest, pytest-cov, ruff (all via `uv sync --group dev`)
- **Lint**: ruff line-length=100, target=py313, select=[B,E,F,I,S,UP,W], E501 ignored

## Hard Rules

- `uv run` for all Python execution — never bare `pip` or `python`
- No `sudo` from agent — collect privileged steps for operator
- Conventional commits with scope: `feat(scope): ...`, `fix(scope): ...`
- Stage explicit paths only — never `git add -A` or `git add .`
- Read before write — never edit a file you haven't read this session

## Architecture

- `mangrove_platform/apparat/` — phase-handler registry (core live code): `api.py` (types), `apparat.py` (registry), `phase_handlers.py`, `horizontal_texture_processor.py`, `guardrails.py`, `src/golding/` (acceleration validator)
- `mangrove_platform/mcp/` — MCP server exposing Apparat as tools (`apparat_server.py`, `apparat_logic.py`, `constraints_engine.py`, `security.py`)
- `tests/` — pytest suite (workspace + apparat + mcp)
- `scripts/` — workspace maintenance and security checks
- `CLAUDE.md` — canonical agent guidance; read it (governance, 3PAA-SHADOW, git identity, data contracts)

## Test Commands

```bash
# Always pass the addopts override on this host (see Gotchas)
uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider"              # all tests
uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider" tests/test_workspace.py -v
uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider" tests/apparat/ -v
uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider" tests/apparat/test_dispatcher.py -v
uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider" tests/apparat/test_phase_handlers.py -v
uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider" tests/test_mcp.py -v
```

Known issue: `tests/test_mcp.py` currently fails on `validate_acceleration` — golding's `CheckResult` exposes `.passed`/`.detail`, but `apparat.py` reads `.success`/`.message`. Pre-existing, unrelated to the MCP security work.

## Checks

`.pre-commit-config.yaml` is declarative only — the `pre-commit` framework is NOT installed and no git pre-commit hook is active. Run the checks directly:

```bash
bash scripts/validate-workspace.sh        # structure + forbidden-patterns + secrets
bash scripts/check-forbidden-patterns.sh  # 3PAA-SHADOW / SUSS / WorkOS / Factory sweep
bash scripts/check-secrets.sh             # secret-pattern scan
bash scripts/check-large-files.sh         # 60 MB corpus-index.tsv guardrail
```

## Commit Format

```
feat(scope): subject ≤72 chars
fix(scope): ...
chore(scope): ...
docs(scope): ...
test(scope): ...
```

## Key Files

- `pyproject.toml` — deps, build, pytest config, ruff config
- `CLAUDE.md` — canonical agent guidance (read before deep work)
- `mangrove_platform/apparat/api.py` — shared types (Phase, GridCell, IProcessor)
- `mangrove_platform/apparat/apparat.py` — phase registry
- `mangrove_platform/mcp/apparat_server.py` — MCP tool definitions
- `mangrove_platform/mcp/security.py` — validation schemas, rate limiter, safety annotations
