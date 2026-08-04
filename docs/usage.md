# Project Usage

Commands for the Mangrove live tree (`/home/cable/series/mangrove/`).

> **Host gotchas** (see `../AGENTS.md` for details): `unset VIRTUAL_ENV` before
> any `uv`/`ruff`/`pytest` run (the shell exports a stale `venv/` path that uv
> ignores), and always pass the pytest addopts override — plain `uv run pytest`
> crashes because this host's Python lacks the `_sqlite3` module, which breaks
> the `--cov` plugin.

## Setup

```bash
unset VIRTUAL_ENV && uv sync --group dev   # install pytest, pytest-cov, ruff
```

## Tests

```bash
unset VIRTUAL_ENV && uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider"                    # all tests
unset VIRTUAL_ENV && uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider" tests/test_workspace.py -v
unset VIRTUAL_ENV && uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider" tests/apparat/test_dispatcher.py -v
unset VIRTUAL_ENV && uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider" tests/test_mcp.py -v
```

Known issue: `tests/test_mcp.py` fails on `validate_acceleration` — golding's
`CheckResult` exposes `.passed`/`.detail`, but `apparat.py` reads
`.success`/`.message`. Pre-existing and unrelated to the MCP security work.

## Lint & Format

```bash
unset VIRTUAL_ENV && uv run ruff check .    # E/F/W/I/UP/B + bandit S rules, line-length 100, py313
unset VIRTUAL_ENV && uv run ruff format .
```

## Workspace Maintenance

```bash
bash scripts/audit_workspace.sh          # counts empty dirs / confirms .gitkeep coverage
bash scripts/validate-workspace.sh       # structure + forbidden-patterns + secrets (shared validate-lib.sh)
bash scripts/check-forbidden-patterns.sh # 3PAA-SHADOW / SUSS / WorkOS / Factory sweep
bash scripts/check-secrets.sh            # secret-pattern scan
bash scripts/check-large-files.sh        # 60 MB corpus-index.tsv guardrail
```

## MCP Server

Server: `mangrove_platform/mcp/apparat_server.py` (FastMCP, 6 tools). Security
layer: `mangrove_platform/mcp/security.py` — Pydantic input validation, a
fixed-window per-tool rate limiter (100 calls/60s), and structured audit
logging. Every tool invocation passes `_gate()` (rate limit then validate), and
state-mutating tools (`run_apparat_phase`, `run_apparat_pipeline`) log
invocations with status.

| Tool | readOnly | destructive | idempotent | openWorld |
|------|----------|-------------|------------|-----------|
| `check_apparat_health` | True | False | True | False |
| `get_apparat_state` | True | False | True | False |
| `list_apparat_phases` | True | False | True | False |
| `run_apparat_phase` | False | False | True | False |
| `run_apparat_pipeline` | False | False | True | False |
| `search_constraints` | True | False | True | False |

Phase names are whitelisted (13 canonical phases in `security.py::ALLOWED_PHASES`);
positional args like `scale:2.0` are allowed via the suffix pattern.

## Apparat

```bash
unset VIRTUAL_ENV && uv run python -m scripts.warmup_apparat                         # primary smoke test (4-stage pipeline + 7/13 phase print)
unset VIRTUAL_ENV && uv run python mangrove_platform/apparat/sisa.py --list-phases   # 13 phases
unset VIRTUAL_ENV && uv run python mangrove_platform/apparat/sisa.py --phase compliance_baseline  # materialize LICENSE/NOTICE/TERMS (deferred)
```

## Build

```bash
unset VIRTUAL_ENV && uv run python -m build   # builds the mangrove package (sources: mangrove_platform per pyproject.toml)
```

## Audit Trail

```bash
head scripts/CODE_REVIEW.md   # canonical review log (F-codes; F2/F3/F4 resolved)
```
