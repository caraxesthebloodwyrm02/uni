---
name: run-apparat
description: build, launch, and verify the Apparat phase-handler registry and MCP server
---

# Run Apparat

This skill bootstraps the Apparat subsystem and verifies its operational health using the runtime warmup routine.

## Prerequisites
- Python 3.13+
- `uv` installed and configured.

## Build & Setup
Ensure the `mangrove` project is synchronized:
```bash
cd /home/cable/series/mangrove
unset VIRTUAL_ENV && uv sync --group dev
```

## Run (Agent Path)
The primary way to drive and verify the Apparat system is via the runtime warmup script. This script bootstraps the SISA registry, verifies all 13 phases, and runs a sample processing pipeline.

```bash
uv run python -m scripts.warmup_apparat
```

### Verify MCP Server
To verify the Apparat MCP server is responsive, you can use the test harness:
```bash
uv run python mangrove_platform/mcp/test_server.py
```

## Run (Human Path)
For interactive exploration, use the SISA CLI to list phases:
```bash
uv run python mangrove_platform/apparat/sisa.py --list-phases
```

## Gotchas
- **Registry Collision**: Apparat uses a dynamic registry. If handlers aren't appearing, ensure `sisa()` is called before the registry is read. See `docs/usage.md` Apparat section for canonical commands.
- **SISA Readiness**: If `SISA bootstrap (ready=False)`, check for missing prerequisite files in the `mangrove_platform/apparat/` directory.
- **MCP Authorization**: The MCP server will fail to load tools unless `~/.claude/AGREEMENT.md` is present and authorizes the server.

## Troubleshooting
- **ModuleNotFoundError: No module named 'mangrove'**: Ensure you are running from the project root (`/home/cable/series/mangrove`) and using `uv run`.
- **SISA Warning: Phases declared but not in Phase enum**: This is normal for the `highlight` phase and other dynamically registered handlers.
