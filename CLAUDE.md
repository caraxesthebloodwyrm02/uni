# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Read Order (Cross-Agent Baseline)
1. `~/.claude/projects/-home-cable-series/memory/MEMORY.md` — operator-curated auto-memory (user-identity, apparat-conventions, SISA-trigger, etc.). Check for applicable context before replying.
2. This file — ecosystem map, build order, data contracts.
3. Closest project `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` to the file being edited.
4. If reachable, the canonical archive at `/home/irfankabir/docs/AGENTS.md` (TUV-001) — currently on an unmounted 538 GB volume.

Notes — read once, then rely on grep:
- `~/WORKFLOW.md`, `~/docs/PROJECT_REGISTRY.yaml`, and `~/.claude/AGREEMENT.md` are referenced from older sessions but **do not exist on this host**. Don't infer them.
- This repo has no `README.md` and no `docs/CLAUDE.md`. This file is the canonical authority for the live tree.

## Live vs canonical

This live working tree (`/home/cable/series/mangrove/`) is a **stub** — the
directories under `finance/`, `intelligence/`, `operations/`, `productivity/`,
`lab/`, `platform/`, `scripts/`, `workspace/`, `routines/` exist but are empty
of code. The **canonical archive** is on the 538 GB volume at
`/home/irfankabir/` (volume UUID `cf656878-be07-4249-b8ba-10fd482aa610`),
where the actual code lives (60+ packages, 34 in `domains/platform/operations/lab/`).
Verify any path or command with `ls <path>` before relying on it — many of
the commands below reference the canonical archive, not the live tree.

## Hard Baseline (survives context compression)
- Read before write — never edit a file you haven't read this session.
- `uv run` for all Python. Never bare `pip` or `python`.
- No `--no-verify`, no `sudo` from agent, no history rewrite without operator consent.
- Conventional commits with scope. Stage explicit paths only — never `git add -A` / `git add .`.
- Identity via `~/.gitconfig` `includeIf` — `caraxesthebloodwyrm02` (primary/CascadeProjects), `irfankabir02` (secondary/grove). The npm scope is `@irfankabir002` (different from the GitHub identities; trailing `2` before the slash). Never set `user.name`/`user.email` ad hoc.

## Interaction Style
Default to conceptual/exploratory mode unless implementation is explicitly requested. Offer genuine, opinionated takes rather than backlogs of fixes or implementation plans.

## Shell & Git Discipline
Before running any automated shell sweeps or multi-command Bash batches, pause and run single, verifiable commands. Wait for confirmation before destructive or sweeping operations.

For git commits: propose the commit plan and message first, then wait for explicit approval before committing. Keep workflows contained on branches.

## Debugging
Never assume or report a bug without verifying against actual file state; corrupted or interleaved tool output is not evidence of a bug.

## Mangrove Ecosystem Overview
A structured multi-project ecosystem organized by domain, serving as the home directory for Prince (Irfan Kabir). The live tree at `/home/cable/series/mangrove/` is a **stub**; the canonical archive lives on the 538 GB volume at `/home/irfankabir/` (volume UUID `cf656878-be07-4249-b8ba-10fd482aa610`), currently unmounted. Verify any path with `ls <path>` before relying on it.

### Directory Map (live tree snapshot)

The live tree holds real code in only a handful of directories; the rest are empty stubs corresponding to canonical rooms.

**Live code (real, executable):**
- `platform/apparat/`: The live Apparat subsystem (see *Live Tree: Apparat Subsystem* below). Modules: `apparat.py` (registry), `sisa.py` (bootstrap CLI), `horizontal_texture_processor.py` (Phase enum + regex dispatcher), `phase_handlers.py` (handler bodies), `review_pack.py` (M5 review-pack generator). Subpkg: `platform/apparat/src/golding/` (acceleration validator).
- `tests/`: Smoke tests for the CLAUDE.md contract (`tests/test_workspace.py`) plus Apparat dispatcher tests (`tests/apparat/`) and golding.validate exit-code tests.
- `scripts/`: `audit_workspace.sh` (counts empty dirs), `build_factbook.py` (regenerates `canon/facts.ndjson` from the canonical volume — currently non-functional because the volume is unmounted), and `corpus-index.tsv` (60 MB generated artifact).
- `canon/`: `facts.ndjson` — 9 verified facts about the canonical archive, each anchored by a reproducible regex.
- `.compliance-hand-off/`: Deferred-plan sidecar for the compliance-baseline phase. `README.md` documents the strategy; `.audit.log` records events.

**Canonical-archive rooms (live `stub` — empty here, populated on the volume):**
- `docs/`: Central knowledge root, identity, and registry on the canonical archive.
- `finance/`: Reward ledgers (`x-change`), contracts (`assistive-agreement-contracts`), and Stripe tools on the canonical archive.
- `intelligence/`: AI infrastructure (`personal-rag` and `GRID`) on the canonical archive.
- `productivity/`: End-user apps (`echoes` and `afloat`) on the canonical archive.
- `operations/`: Security (`workspace-trust-auditor`), portfolio control, and workspace maintenance on the canonical archive.
- `lab/`: 34-package `uv` experiment ecosystem on the canonical archive (hub-and-spoke on `lab-common`); most active: `silver`, `goblet`, `wikidex`, `mistral-test`, `painterly`, `painterly-perception`. Note: `python-craft/` is **collaborator-owned** (author `shinychoes`) — out of audit-edit scope. Has its own canonical `lab/CLAUDE.md` and `lab/SPINES.md` (cross-package edge map) — read those before touching anything under `lab/`.
- `workspace/`: GRID Slider Compass (read-only Node/JS navigation compass) on the canonical archive.
- `routines/`: Scheduled/cron agent routines on the canonical archive.

## Common Commands

### Live Tree (this repo, executable now)

The only commands that actually work against `/home/cable/series/mangrove/` today:

```bash
# Build / deps
uv sync --group dev                                                # install pytest, pytest-cov, ruff

# Tests
uv run pytest                                                      # all tests (test_workspace.py + apparat/)
uv run pytest tests/test_workspace.py -v                           # CLAUDE.md smoke contract
uv run pytest tests/apparat/test_dispatcher.py -v                  # regex dispatcher

# Lint
uv run ruff check .                                                # E/F/W/I/UP/B, line-length 100, py313
uv run ruff format .

# Workspace maintenance
bash scripts/audit_workspace.sh                                    # Verify that all directories are properly populated or have a .gitkeep

# Apparat warmup & verification
uv run python -m mangrove.scripts.warmup_apparat                   # Primary smoke test for Apparat subsystem
uv run python platform/apparat/sisa.py --list-phases               # 12 phases
uv run python platform/apparat/sisa.py --phase compliance_baseline # materializes LICENSE/NOTICE/TERMS_OF_ENGAGEMENT.md
                                                                    #   (currently deferred — see .compliance-hand-off/README.md)
```

Note: `uv run python -m build` builds the `platform` package, as declared in `pyproject.toml`.

### Workspace Maintenance (canonical archive only)
```bash
bash scripts/morning-briefing.sh      # daily orientation
bash scripts/audit_workspace.sh       # full workspace audit
bash scripts/git-hygiene.sh           # clean up git state
bash scripts/apply-hardening.sh       # apply OS hardening
```

### Development & Build Order (canonical archive only)
1. **Shared Types:** `cd platform/CascadeProjects/Components/shared-types && npm install && npm run build`
2. **MCP Servers:** `npm install` in individual directories under `platform/CascadeProjects/Tools/MCPServers/`.
3. **Python Projects:** `uv sync --group dev` (use `uv run` for all execution — never bare `python` or `pip`).
4. **Next.js Apps:** `npm run dev` or `npm run build` in `productivity/afloat` or `productivity/hogsmade`.

### Project-Specific Tests/Lint (canonical archive only)
```bash
cd productivity/echoes && make test              # pytest
cd productivity/afloat && npm test               # vitest
cd finance/x-change && uv run pytest
cd intelligence/personal-rag && uv run pytest
cd platform/dep-mapper && make check             # lint + test
cd platform/gruff && npm run test
```

### Running a Single Test (canonical archive only)
Three test runners are in play — match the invocation to the project:
```bash
# pytest projects (echoes, dep-mapper, x-change, personal-rag)
uv run pytest tests/test_file.py::test_name -v          # one test
uv run pytest tests/test_file.py -k "substring"         # match by name

# afloat — vitest (npm test = `vitest run`)
npm test -- tests/smoke.test.ts                         # one file
npx vitest run -t "test name substring"                 # match by name

# gruff — node built-in runner (no vitest/jest)
node --import tsx --test src/path/file.test.ts          # one file
```

### Key Project Commands (canonical archive only)
```bash
# x-change: reward ledger API — 8788 port policy lives in Governance & Safety
cd finance/x-change && uv run uvicorn xchange.app:app
uv run --group mcp python -m xchange.xchange_mcp    # read-only MCP over SQLite

# personal-rag: local RAG pipeline (Ollama + ChromaDB, no external APIs)
cd intelligence/personal-rag && uv run python main.py
uv run python mcp_mod/server.py                     # MCP server entry point

# GRID: dual API servers
bash scripts/run-grid.sh                            # Mothership :8080 + Gateway :8000

# afloat: workflow web app
cd productivity/afloat && npm run dev

# workspace-trust-auditor
node operations/workspace-trust-auditor/src/cli.js
node operations/workspace-trust-auditor/src/web-server.js
```

## Technical Architecture & Dependencies

### Live Tree: Apparat Subsystem

The core live code in this tree is the Apparat subsystem at `platform/apparat/`. It is a high-accuracy, type-safe dynamic phase-handler registry for grid-cell processing.

- **api.py** — The foundational source of truth. Defines shared types and protocols: `Phase` (Enum), `GridCell` (frozen dataclass), `InputProcessOutput` (I/O bridge), `IProcessor` (Protocol), and `PhaseHandler` (Protocol). This module resolves all circular dependencies.
- **apparat.py** — Typed Registry. `PHASE_REGISTRY` maps phase names to `(handler, signature, param_map)`. Provides `@register_phase_handler` for type-safe registration and dynamic parameter mapping.
- **horizontal_texture_processor.py** — Main orchestrator implementing `IProcessor`. Uses a regex-driven dispatcher (`name:arg1,arg2`) that maps positional arguments to named parameters via the registry's `param_map` before executing handlers.
- **phase_handlers.py** — Concrete implementation of phase logic. Adheres to the `PhaseHandler` protocol. Optimized for performance by using direct `GridCell` instantiation instead of `dataclasses.replace()`.
- **platform/mcp/apparat_logic.py** — The MCP bridge. Manages a `_GLOBAL_PROCESSOR` singleton to maintain grid state across independent tool calls and initializes the registry.
- **platform/mcp/apparat_server.py** — FastMCP server exposing Apparat as a toolset (`list_apparat_phases`, `run_apparat_phase`, `search_constraints`).
- **review_pack.py** — M5 review-pack generator. Collects Phase 1 (workspace synthesis) and Phase 2 (tripwire tests, regex dispatcher description) to produce `REVIEW_PACK.md`.
- **golding subpkg** — `platform/apparat/src/golding/` provides acceleration validation and baseline normalization checks.

The `tests/apparat/` directory exercises the dispatcher and validation logic.

### Data Flow
`productivity/echoes` (runtime logs) → `~/.echoes/audit.ndjson` → `intelligence/personal-rag` (ingest) → Session Intelligence (GRID)

### Key Systems
- **x-change:** FastAPI reward ledger with Stripe webhook integration. State machine: `drafted → earned → payment_pending → payment_confirmed → student_acknowledged` (with `review_requested` branch at any point; `domain.py` is the only valid mutator). Missing Stripe metadata goes to `support_signals`, never dropped.
- **personal-rag:** Zero-abstraction local RAG. Chromadb + Ollama (`nomic-embed-text-v2-moe`). Epistemic gravity scoring — `QUESTION` chunks gain urgency over time (λ = −0.010); `DECISION`/`CONSTRAINT` are near-permanent (λ = +0.001). Four-stage pipeline: ingest → classify → retrieve → generate.
- **GRID Cognitive Engine:** Dual API servers — Mothership at `:8080`, Gateway at `:8000`. MCP-connected.
- **echoes:** FastAPI + Docker agent runtime. Emits structured audit events to `~/.echoes/audit.ndjson`.

### Toolchain
- **Python:** 3.13+, `uv` for all dependency management. `uv run` for all execution.
- **Node:** `npm` for most projects; `pnpm` only for `mcp-tool-experiment`.
- **OS packages:** `apt` only. No `sudo` from agent — collect privileged steps for operator.
- **Identity:** Managed via `~/.gitconfig` `includeIf`.
  - `caraxesthebloodwyrm02` (Primary/CascadeProjects)
  - `irfankabir02` (secondary/grove)
  - npm scope: `@irfankabir002` (verified at `domains/platform/gruff/package.json:2`)

### MCP
MCP servers are **disabled by default** (no `~/.claude/AGREEMENT.md` exists on this host — that reference is operator-deferred). Re-admit explicitly per task. Local servers (echoes, personal-rag, grid-server, pulse, glimpse, seeds, eligibility) are local-only — remote agents cannot reach them.

## Commit Conventions
Conventional commits are required. Scope is mandatory for non-trivial changes.

```
feat(scope): subject ≤72 chars
fix(scope): ...
chore(scope): ...
docs(scope): ...
test(scope): ...
refactor(scope): ...
```

Stage explicit paths only. Never `git add -A` or `git add .`. Identity comes from `~/.gitconfig` `includeIf` — never set `user.name`/`user.email` ad hoc.

## Governance & Safety
- **Trust Contract (TUV-001):** Canonical rules live at `/home/irfankabir/docs/AGENTS.md` on the canonical archive (volume). The legacy reference `/mnt/arch_data/home/caraxes/seed/templates/development-contract.md` is on the unmounted Arch partition and may not resolve on this host.
- **3PAA-SHADOW Containment:** Significant Challenge mandate active.
  - **Hard Deny:** `factory.ai`, `cursor.com`, `cursor.sh`, `workos.com`.
  - **Blocked Ports:** 54621, 8081, 40925. Port **8788** is blocked for all uses **except** x-change production (bind locally; do not expose).
  - **Forbidden Tokens:** `WorkOS`, `Factory`.
  - **SUSS Path Deny:** HARD-DENIED at all levels. Git hooks block commit/push. `.gitignore` prevents tracking.
  - **Override:** `GIT_ALLOW_SUSS=1 git commit/push` (sudo-equivalent; audit trail written).
- **Privileges:** No `sudo`. Collect privileged steps for operator execution.
- **`DO-NOT.html`** lives on the canonical archive at `domains/platform/finance/DO-NOT.html` (volume) — not in the live `finance/` stub. It encodes 9 payment hardlines that apply to every component in the finance package.
