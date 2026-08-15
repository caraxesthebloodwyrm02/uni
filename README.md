# Mangrove

Welcome to the Mangrove repository.

## Overview
This repository currently acts as a **live stub** for the canonical Apparat subsystem and MCP bridge.

The real code present in this tree is:
- **`mangrove_platform/apparat/`**: The core Apparat subsystem (a high-accuracy, type-safe dynamic phase-handler registry for grid-cell processing).
- **`mangrove_platform/mcp/`**: The MCP (Model Context Protocol) bridge and FastMCP server exposing Apparat tools.

Other domains (`finance`, `intelligence`, `operations`, etc.) reside on a canonical volume and are omitted from this live tracking to ensure CI independence.

## Architecture and Guidelines
This project is governed by strict, agentic design principles. Before interacting with or modifying the codebase, it is mandatory to review the following documents:
- [CLAUDE.md](./CLAUDE.md) — The canonical authority for the live tree, containing the ecosystem map, interactions style, host-specific gotchas, and hard baselines.
- [AGENTS.md](./AGENTS.md) — The immediate quick start, python/uv instructions, test commands, and project facts.
- [TERMS_OF_ENGAGEMENT.md](./TERMS_OF_ENGAGEMENT.md) — The formal guidelines.

## Quick Start
```bash
unset VIRTUAL_ENV && uv sync --group dev
unset VIRTUAL_ENV && uv run python -m pytest -o "addopts=-p no:anyio -p no:cacheprovider" -v
```

See `AGENTS.md` for a comprehensive list of test and maintenance scripts.
