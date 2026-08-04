# Mangrove Codebase (Botanical Garden)
This directory is digital botanical garden environment where species co-exist within a cyclical ecosystem resembling practical systema and logic with code

It is intentionally minimal: the authoritative guidance for agents working on the
Mangrove live tree lives in [`../CLAUDE.md`](../CLAUDE.md). This README is a
landing page so external tools (GitHub's "About" pane, grep agents, and
developer humans) can find their way to the canonical documents.

## Where to start

- [`../CLAUDE.md`](../CLAUDE.md) — read this first if you are a Claude agent.
  It pins the **Hard Baseline** (uv run only, no sudo, no ad-hoc git identity),
  the **Directory Map**, the **Common Commands** split between live and
  canonical-archive, and the **Governance & Safety** rules (TUV-001,
  3PAA-SHADOW, port 8788 policy, DO-NOT.html).
- [`../.compliance-hand-off/README.md`](../.compliance-hand-off/README.md) —
  the compliance-baseline hand-off record. `LICENSE`, `NOTICE`, and
  `TERMS_OF_ENGAGEMENT.md` are materialised at the live tree root; the
  artefacts will be ported to the canonical archive when the 538 GB volume
  (UUID `cf656878-be07-4249-b8ba-10fd482aa610`) becomes reachable.
- [`../.compliance-hand-off/.audit.log`](../.compliance-hand-off/.audit.log) —
  append-only event log for hand-off events. The source of truth for what was
  shipped to `/home/irfankabir/` when the canonical volume mounts.

## Project layout

The Mangrove working tree at `/home/cable/series/mangrove/` is a **stub** by
design. The actual code for most domains (`finance/`, `intelligence/`,
`productivity/`, `operations/`, `lab/`, `workspace/`, `routines/`) lives on
the canonical archive volume at `/home/irfankabir/` (UUID
`cf656878-be07-4249-b8ba-10fd482aa610`), which is currently unmounted from
this session. The live tree holds:

- `mangrove_platform/apparat/` — the only substantial live code
  (phase-handler registry, SISA bootstrap, dispatcher, golding validator).
- `mangrove_platform/mcp/` — FastMCP server exposing Apparat as 6 tools, with a
  security layer (`security.py`: Pydantic validation, rate limiting, audit
  logging).
- `tests/` — smoke tests for the `CLAUDE.md` contract and Apparat dispatch
  tests.
- `scripts/` — `validate_workspace.py` (structure, secrets, forbidden
  patterns, large-file checks), `build_factbook.py`, and branch-audit
  tooling (`prune-stale-branches.sh`).
- `.compliance-hand-off/` — deferred-compliance sidecar (see above).

For a live snapshot of every directory under the live tree, see the **Directory
Map** section of [`../CLAUDE.md`](../CLAUDE.md).

## Live tree quick reference

The only commands that actually work against `/home/cable/series/mangrove/`
today:

```bash
unset VIRTUAL_ENV && uv sync --group dev                                              # install pytest, pytest-cov, ruff
unset VIRTUAL_ENV && uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider"  # all tests (see usage.md)
unset VIRTUAL_ENV && uv run ruff check .                                              # lint
unset VIRTUAL_ENV && uv run python mangrove_platform/apparat/sisa.py --list-phases   # 13 Apparat phases
```

Note: plain `uv run pytest` crashes on this host (missing `_sqlite3` breaks the
`--cov` plugin); always pass the addopts override shown above. Full commands are
in [`usage.md`](usage.md).

A complete breakdown — including split between live and canonical-archive
commands — is in the **Common Commands** section of
[`../CLAUDE.md`](../CLAUDE.md).

## Governance

This project enforces the following non-negotiables. The full text is in
[`../CLAUDE.md`](../CLAUDE.md) under **Hard Baseline**, **Commit Conventions**,
and **Governance & Safety**:

- All Python execution via `uv run`. Never bare `pip` or `python`.
- No `sudo` from agent. Collect privileged steps for operator execution.
- Conventional commits with scope. Stage explicit paths only — never
  `git add -A` / `git add .`.
- Identity via `~/.gitconfig` `includeIf`. Never set `user.name` /
  `user.email` ad hoc.
- 3PAA-SHADOW containment: hard-deny `factory.ai`, `cursor.com`,
  `cursor.sh`, `workos.com`; blocked ports 54621, 8081, 40925; port 8788
  reserved for x-change production.
- Trust Contract (TUV-001) at
  `/home/irfankabir/docs/AGENTS.md` on the canonical archive (volume
  unmounted from this session).

## License

The full MIT license text is materialised at the live tree root
(`LICENSE`, `NOTICE`, `TERMS_OF_ENGAGEMENT.md`) by the Apparat
`compliance_baseline` phase
(`mangrove_platform/apparat/phase_handlers.py::compliance_baseline_handler`).
A stub reference is in `../pyproject.toml::license` as `{ text = "MIT" }`
(PEP 639 mixed-object form).
