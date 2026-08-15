# Mangrove

A type-safe, dynamic phase-handler registry for grid-cell processing, exposed
over MCP (Model Context Protocol).

## Overview

The code that lives in this repository:

- **`mangrove_platform/apparat/`** — the Apparat subsystem: a dynamic
  phase-handler registry (`apparat.py`), the orchestrator that parses and
  dispatches phase syntax (`horizontal_texture_processor.py`), the concrete
  phase logic (`phase_handlers.py`), and `sisa.py`, the bootstrap health
  check (`uv run sisa`).
- **`mangrove_platform/mcp/`** — the MCP bridge: `apparat_server.py` (the
  FastMCP server exposing Apparat's tools), `apparat_logic.py` (per-affiliate
  processor state), and `security.py` (request validation, rate limiting,
  audit logging).
- **`platform/`**, **`scripts/`** — workspace tooling (dependency hygiene,
  branch pruning, workspace validation) invoked by CI.

`CLAUDE.md`/`AGENTS.md` are intentionally **not tracked** in this repository
(kept local-only to the working tree that authors them) — see
`TERMS_OF_ENGAGEMENT.md` below for the tracked authority chain instead.

## Authority documents

- **[TERMS_OF_ENGAGEMENT.md](./TERMS_OF_ENGAGEMENT.md)** — authority
  precedence, live-vs-canonical surface, hard baseline, governance.
- **[docs/usage.md](./docs/usage.md)** — canonical test/lint/setup commands
  and host-specific gotchas.
- **[docs/SECURITY.md](./docs/SECURITY.md)**,
  **[docs/security-plan.md](./docs/security-plan.md)** — security posture
  and the MCP request-validation model.

## Quick start

```bash
unset VIRTUAL_ENV && uv sync --group dev
unset VIRTUAL_ENV && uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider"
unset VIRTUAL_ENV && uv run sisa   # bootstrap health check
```

`unset VIRTUAL_ENV` guards against a stale `venv/` path some shells export.
See [docs/usage.md](./docs/usage.md) for the full command set, including
per-file/per-class test invocations and lint/format targets.

## License

MIT — see [LICENSE](./LICENSE).
