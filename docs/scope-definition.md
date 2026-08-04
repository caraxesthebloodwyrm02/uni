# Most Applicable Scope Definition

> **Status (2026-08-04):** Scope approved and in progress. Items 1-5 of the
> IN SCOPE list are implemented (`mangrove_platform/mcp/security.py` +
> `apparat_server.py`); the test/bandit/CI follow-ups are pending.

## Project Context

The Mangrove project is a **small-to-medium Python workspace** with:
- **Core**: Apparat phase-handler registry (13 phases, ~500 lines)
- **MCP Server**: 7 tools exposing Apparat functionality
- **Dependencies**: Minimal (`mcp`, `pydantic` runtime)
- **Purpose**: Grid-cell processing with validation pipeline

---

## Recommended Scope: **MCP Tool Security Hardening**

### Why This Scope

| Factor | Assessment |
|--------|------------|
| **Project Size** | Small (~2000 LOC total) |
| **Complexity** | Low-Medium (phase registry pattern) |
| **Risk Surface** | MCP tools are the primary external interface |
| **Value/Effort** | High security ROI for moderate effort |

### Scope Boundaries

**IN SCOPE:**
1. Input validation for all 7 MCP tools
2. Safety annotations on tool registrations
3. Structured logging for audit trail
4. Dependency updates (pydantic, cryptography)
5. Basic rate limiting

**OUT OF SCOPE (for now):**
- Browser automation (not needed yet)
- OAuth 2.1 (only for remote deployment)
- Container sandboxing (overkill for local use)
- OpenTelemetry (premature optimization)

---

## Detailed Scope Definition

### 1. Input Validation Layer

**What**: Add Pydantic models to validate all tool inputs

**Why**: Phase names like `scale:2.0` are parsed via regex; injection risk exists

**Implementation**:
```python
# Example for run_apparat_phase
class PhaseRequest(BaseModel):
    phase: str = Field(..., pattern=r"^[a-zA-Z_]+(?::[0-9.,]+)?$")
    width: int = Field(4, ge=1, le=100)
    height: int = Field(4, ge=1, le=100)

    @validator("phase")
    def validate_phase_name(cls, v):
        base = v.split(":")[0]
        allowed = {
            "initiate",
            "quantize",
            "combine",
            "render",
            "complete",
            "normalize",
            "scale",
            "clamp",
            "filter",
            "invert",
            "highlight",
            "compliance_baseline",
            "validate_acceleration",
        }
        if base not in allowed:
            raise ValueError(f"Unknown phase: {base}")
        return v
```

**Scope Limits**:
- Validate at tool entry point only
- No deep validation of phase parameters (let handlers validate)
- Whitelist approach (explicit allowed values)

### 2. Safety Annotations

**What**: Add MCP standard annotations to all tool registrations

**Why**: Enables clients to make informed trust decisions

**Implementation**:
```python
@mcp.tool(
    annotations={
        "readOnlyHint": False,  # Tools modify grid state
        "destructiveHint": False,  # Non-destructive (state is replaceable)
        "idempotentHint": True,  # Same input = same output
        "openWorldHint": False,  # Closed system, no external calls
    }
)
def run_apparat_phase(phase: str, width: int = 4, height: int = 4): ...
```

**Tool-Specific Annotations**:

| Tool | readOnly | destructive | idempotent | openWorld |
|------|----------|-------------|------------|-----------|
| `check_apparat_health` | True | False | True | False |
| `get_apparat_state` | True | False | True | False |
| `list_apparat_phases` | True | False | True | False |
| `run_apparat_phase` | False | False | True | False |
| `run_apparat_pipeline` | False | False | True | False |
| `search_constraints` | True | False | True | False |

### 3. Structured Logging

**What**: Add audit logging for all tool invocations

**Why**: Compliance trail, debugging, security monitoring

**Implementation**:
```python
import logging
from datetime import datetime, timezone

logger = logging.getLogger("mangrove.mcp")


def log_tool_invocation(tool_name: str, params: dict, result: dict):
    """Log tool invocation for audit trail."""
    logger.info(
        "tool_invocation",
        extra={
            "tool": tool_name,
            "params": params,
            "status": result.get("status"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cell_count": len(result.get("result", [])),
        },
    )
```

**Scope Limits**:
- Log at tool entry/exit only
- No logging of full grid data (too large)
- Structured format for grep/analysis

### 4. Dependency Updates

**What**: Add minimal security-relevant dependencies

**Why**: Pydantic for validation, cryptography for future OAuth

**Implementation**:
```toml
[project]
dependencies = [
    "mcp>=2.0.0,<3",
    "pydantic>=2.0,<3",      # Input validation
]

[dependency-groups]
dev = [
    "pytest-cov>=7.1.0,<8",
    "pytest>=8.3.0,<9",
    "ruff>=0.4.0,<1",
    "bandit>=1.7,<2",        # Security linting
]
```

**Scope Limits**:
- Only add what's immediately needed
- No browser automation libs yet
- No HTTP client (httpx) unless needed

### 5. Basic Rate Limiting

**What**: Simple in-memory rate limiting per tool

**Why**: Prevent abuse, resource exhaustion

**Implementation**:
```python
from collections import defaultdict
from time import time


class RateLimiter:
    def __init__(self, max_calls: int = 100, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window = window_seconds
        self.calls = defaultdict(list)

    def allow(self, tool_name: str) -> bool:
        now = time()
        self.calls[tool_name] = [t for t in self.calls[tool_name] if now - t < self.window]
        if len(self.calls[tool_name]) >= self.max_calls:
            return False
        self.calls[tool_name].append(now)
        return True
```

**Scope Limits**:
- In-memory only (no persistence)
- Fixed window (no sliding window)
- Per-tool only (no per-user)

---

## What This Scope Achieves

### Security Posture

| Before | After |
|--------|-------|
| No input validation | Pydantic schemas on all tools |
| No safety metadata | Standard MCP annotations |
| No audit trail | Structured logging |
| Minimal deps | Security linting in CI |

### Risk Reduction

| Risk | Mitigation |
|------|------------|
| Phase name injection | Whitelist validation |
| Tool misuse | Safety annotations inform clients |
| Undetected abuse | Audit logging |
| Dependency vulnerabilities | Bandit scanning |

### Compliance Alignment

- **MCP 2026-07-28**: Tool safety annotations required
- **OWASP**: Input validation, least privilege
- **NSA Guidance**: Audit logging for tool calls

---

## Implementation Effort

| Task | Effort | Priority |
|------|--------|----------|
| Pydantic schemas | 2-3 hours | High |
| Safety annotations | 30 minutes | High |
| Structured logging | 1-2 hours | High |
| Dependency updates | 30 minutes | Medium |
| Rate limiting | 1 hour | Medium |
| **Total** | **5-7 hours** | |

---

## Success Criteria

Status as of 2026-08-04:

1. [x] All 7 MCP tools have Pydantic validation
2. [x] All tools have safety annotations
3. [x] Audit log captures all invocations
4. [→] `bandit` — deferred to next session. Ruff's flake8-bandit (`S`) rules are
      already wired in `[tool.ruff.lint].select` and provide equivalent coverage;
      no added value in installing the `bandit` tool as a separate dev dep.
      Revisit if a specific bandit rule is needed that ruff's `S` does not cover.
5. [~] Existing tests still pass (all pass except pre-existing `validate_acceleration`
      golding bug — `CheckResult.passed` vs `.success`; unrelated to this scope)

---

## Future Scope (Not Now)

When to expand scope:
- **Remote deployment**: Add OAuth 2.1
- **Browser tools**: Add pydoll/playwright
- **Multi-tenant**: Add per-user rate limiting
- **Production**: Add OpenTelemetry tracing
- **High scale**: Add container sandboxing
