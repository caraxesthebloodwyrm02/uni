# Dependency Management

## Overview

Simplified dependency management with CI automation and monthly Dependabot updates.

## Configuration

**Dependabot**: `.github/dependabot.yml`
- Monthly dependency updates (Mondays 09:00 UTC)
- Blocks major `mcp` updates (critical dependency)
- Labels: `dependencies`, `python`

**CI Pipeline**: `.github/workflows/ci.yml`
- Runs on push/PR to master/main
- Lint check, test execution, dependency hygiene
- Uploads dependency metrics as artifacts

## Current Dependencies

**Main**: `mcp>=2.0.0`  
**Dev**: `pytest>=8.3.0,<9`, `pytest-cov>=7.1.0,<8`, `ruff>=0.4.0,<1`

## Manual Updates

```bash
# Check for updates
uv pip list --outdated

# Update specific package
uv add <package>@latest

# Update all dependencies
uv sync --upgrade

# Run tests after updates
uv run pytest
```
