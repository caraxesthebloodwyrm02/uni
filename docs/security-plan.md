# Mangrove Security & MCP Enhancement Plan

## Executive Summary

This plan addresses three interconnected areas for the Mangrove project:
1. Browser automation safety and security tools
2. MCP configuration adaptation from Anthropic's 2026-07-28 specification
3. External dependency recommendations optimized for safety/security scope

---

## 1. Browser Automation Safety & Security

### Current State
The Mangrove project doesn't currently include browser automation, but the MCP server could benefit from browser-based tools for monitoring, testing, or data collection.

### Recommended Tools & Libraries

#### Tier 1: Stealth-First Browser Automation (Recommended)
| Library | Purpose | Security Features |
|---------|---------|-------------------|
| **pydoll** | CDP-native automation | No WebDriver flag, Bezier mouse movement, humanized timing |
| **playwright** | General automation | Built-in wait mechanisms, network interception |
| **seleniumbase** | Anti-detection | UC mode, undetected chromedriver |

#### Tier 2: Security Hardening
| Tool | Purpose |
|------|---------|
| **curl-impersonate** | TLS fingerprint impersonation |
| **tls-client** | HTTP client with browser-like TLS |
| **camoufox** | Firefox with stealth patches |

### Security Best Practices for Browser Integration

```python
# Example: Secure browser automation pattern
from dataclasses import dataclass
from enum import Enum


class SafetyLevel(Enum):
    LOW = "low"  # Basic automation
    MEDIUM = "medium"  # With proxy rotation
    HIGH = "high"  # Full stealth stack


@dataclass
class BrowserConfig:
    safety_level: SafetyLevel
    use_proxy: bool = False
    humanize_delays: bool = True
    screenshot_on_error: bool = True
    max_retries: int = 3
```

### Implementation Considerations

1. **Proxy Management**: Use residential proxies for external requests
2. **Session Isolation**: Separate browser contexts per tool invocation
3. **Audit Logging**: Log all browser interactions for compliance
4. **Rate Limiting**: Respect target site rate limits
5. **Error Recovery**: Graceful degradation when detection occurs

---

## 2. MCP Configuration Adaptation

### Current Implementation Analysis

> **Status (2026-08-04):** Phase 1 is implemented — validation, safety
> annotations, and audit logging are live in
> `mangrove_platform/mcp/security.py` + `mangrove_platform/mcp/apparat_server.py`.
> The analysis below is retained as the historical baseline for why the work
> was scoped.

**Existing code** (`mangrove_platform/mcp/apparat_server.py`):
- Uses `mcp.server.fastmcp.FastMCP` (v2 compatible)
- 6 tools registered via `@mcp.tool()` decorator
- No input validation schemas (now added: Pydantic models in `security.py`)
- No safety annotations (now added: `safety_annotations()` on all 6 tools)
- No transport configuration

### Anthropic 2026-07-28 Specification Updates

Key changes relevant to Mangrove:

| Feature | Old | New | Impact |
|---------|-----|-----|--------|
| Sessions | Stateful `Mcp-Session-Id` | Stateless requests | Simpler scaling |
| Transport | Separate `/sse` + `/messages` | Single `/mcp` endpoint | Reduced attack surface |
| Authorization | Optional | OAuth 2.1 required for remote | Better security |
| Tool Safety | Ad-hoc | Standardized annotations | Clear trust boundaries |

### Recommended Adaptations

#### A. Tool Registration with Safety Annotations

```python
# Current (no annotations)
@mcp.tool()
def run_apparat_phase(phase: str, width: int = 4, height: int = 4): ...


# Proposed (with safety metadata)
@mcp.tool(
    annotations={
        "readOnlyHint": False,  # Modifies state
        "destructiveHint": False,  # Not destructive
        "idempotentHint": True,  # Same input = same output
        "openWorldHint": False,  # Closed system
    }
)
def run_apparat_phase(phase: str, width: int = 4, height: int = 4): ...
```

> **Canonical source of the annotation vocabulary:** `mangrove_platform/mcp/security.py`
> defines the same four keys as the `ToolSafety` enum (`READ_ONLY`/`DESTRUCTIVE`/
> `IDEMPOTENT`/`OPEN_WORLD`) and exposes the helper
> `safety_annotations(read_only=..., destructive=..., idempotent=..., open_world=...)`
> that returns the dict above. Production code should call the helper rather
> than hand-rolling the dict — see `apparat_server.py`'s six `@mcp.tool(...)`
> decorators for the live pattern. If MCP ever adds a fifth annotation, only
> `security.ToolSafety` and the helper need to change.

#### B. Input Validation with Pydantic

```python
from pydantic import BaseModel, Field, validator


class PhaseRequest(BaseModel):
    phase: str = Field(..., description="Phase name (e.g., 'initiate', 'scale:2.0')")
    width: int = Field(4, ge=1, le=100, description="Grid width")
    height: int = Field(4, ge=1, le=100, description="Grid height")

    @validator("phase")
    def validate_phase(cls, v):
        # Whitelist validation
        allowed_phases = {"initiate", "quantize", "combine", "render", "complete"}
        base_phase = v.split(":")[0]
        if base_phase not in allowed_phases:
            raise ValueError(f"Invalid phase: {v}")
        return v
```

#### C. Transport Configuration

```python
# For local development (stdio)
mcp = FastMCP("Apparat-Server")

# For remote deployment (Streamable HTTP)
mcp = FastMCP(
    "Apparat-Server",
    stateless_http=True,  # 2026-07-28 spec
    port=8080,
)
```

#### D. Security Headers for HTTP Transport

```python
# Add to server configuration
SECURITY_HEADERS = {
    "Mcp-Method": "tools/call",  # For gateway routing
    "Mcp-Name": "run_apparat_phase",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}
```

---

## 3. External Dependency Recommendations

### Current Dependencies
- **Runtime**: `mcp>=2.0.0,<3`
- **Dev**: `pytest`, `pytest-cov`, `ruff`

### Recommended Additions for Safety/Security Scope

#### Tier 1: Essential Security Libraries

| Package | Version | Purpose | Justification |
|---------|---------|---------|---------------|
| `pydantic` | `>=2.0,<3` | Input validation | MCP SDK already uses it; add explicit dependency |
| `cryptography` | `>=42.0,<43` | TLS, JWT, signing | Required for OAuth 2.1, tool attestation |
| `httpx` | `>=0.27,<1` | HTTP client | MCP SDK dependency; use for outbound requests |
| `tenacity` | `>=8.0,<9` | Retry logic | Resilient tool execution |

#### Tier 2: Browser Automation (If Needed)

| Package | Version | Purpose | Justification |
|---------|---------|---------|---------------|
| `pydoll` | `>=2.0,<3` | Stealth browser | CDP-native, no WebDriver detection |
| `playwright` | `>=1.40,<2` | General automation | Well-maintained, good security track record |

#### Tier 3: Monitoring & Audit

| Package | Version | Purpose | Justification |
|---------|---------|---------|---------------|
| `structlog` | `>=24.0,<25` | Structured logging | Audit trail for tool invocations |
| `opentelemetry-api` | `>=1.0,<2` | Tracing | Already in MCP SDK; extend to app code |

### Dependency Security Considerations

```toml
# Updated pyproject.toml dependencies
[project]
dependencies = [
    "mcp>=2.0.0,<3",
    "pydantic>=2.0,<3",          # Input validation
    "cryptography>=42.0,<43",    # Security primitives
    "httpx>=0.27,<1",            # HTTP client
    "tenacity>=8.0,<9",          # Resilience
]

[dependency-groups]
dev = [
    "pytest-cov>=7.1.0,<8",
    "pytest>=8.3.0,<9",
    "ruff>=0.4.0,<1",
    "bandit>=1.7,<2",            # Security linting
    "safety>=3.0,<4",            # Vulnerability scanning
]
```

---

## 4. Safety & Security Architecture

### Stream Safety

```python
# Example: Secure stream processing
from contextlib import asynccontextmanager
from typing import AsyncGenerator


@asynccontextmanager
async def safe_stream_processor():
    """Context manager for safe stream processing."""
    try:
        # Validate inputs before processing
        # Set up audit logging
        # Configure timeouts
        yield
    except Exception as e:
        # Log security event
        # Clean up resources
        # Notify monitoring
        raise
```

### Thread Safety

```python
import threading
from contextlib import contextmanager


class ThreadSafeProcessor:
    """Thread-safe processor with proper locking."""

    def __init__(self):
        self._lock = threading.RLock()
        self._state = {}

    @contextmanager
    def safe_operation(self):
        """Ensure thread-safe state modifications."""
        with self._lock:
            # Snapshot state before modification
            old_state = self._state.copy()
            try:
                yield
            except Exception:
                # Rollback on failure
                self._state = old_state
                raise
```

### Architecture Security

```
+-------------------------------------------------------------+
|                    Security Layers                          |
+-------------------------------------------------------------+
|  Layer 1: Input Validation (Pydantic schemas)              |
+-------------------------------------------------------------+
|  Layer 2: Authorization (OAuth 2.1 for remote)             |
+-------------------------------------------------------------+
|  Layer 3: Sandboxing (Container/process isolation)          |
+-------------------------------------------------------------+
|  Layer 4: Monitoring (Audit logs, tracing)                  |
+-------------------------------------------------------------+
|  Layer 5: Rate Limiting (Per-tool, per-user)                |
+-------------------------------------------------------------+
```

---

## 5. Implementation Roadmap

### Phase 1: MCP Security Hardening (Week 1-2) — DONE
- [x] Add Pydantic validation schemas to all tools (`security.py`: `PhaseRequest`, `PipelineRequest`, `ConstraintRequest`, `GridRequest`)
- [x] Add safety annotations to tool registrations (`safety_annotations()` on all 6 tools)
- [x] Implement input sanitization for phase names (`ALLOWED_PHASES` whitelist + `PHASE_ARG_PATTERN`)
- [x] Add structured logging for tool invocations (`log_tool_invocation()`)

### Phase 2: Transport Security (Week 3-4)
- [ ] Configure stateless HTTP transport
- [ ] Add security headers middleware
- [ ] Implement OAuth 2.1 for remote deployment
- [ ] Add rate limiting

### Phase 3: Browser Integration (Optional, Week 5-6)
- [ ] Evaluate pydoll vs playwright for stealth needs
- [ ] Implement browser automation safety wrapper
- [ ] Add proxy management
- [ ] Create audit logging for browser actions

### Phase 4: Monitoring & Compliance (Week 7-8)
- [ ] Integrate OpenTelemetry tracing
- [ ] Add security event monitoring
- [ ] Create compliance audit trails
- [ ] Document security architecture

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tool poisoning via descriptions | Medium | High | Whitelist validation, description sanitization |
| STDIO injection (CVE-2026-30623) | Low | Critical | Use HTTP transport, validate config |
| Session hijacking | Low | High | Stateless design, token validation |
| Resource exhaustion | Medium | Medium | Timeouts, rate limits, quotas |
| Dependency vulnerabilities | Medium | High | Pin versions, regular audits |

---

## 7. Success Metrics

- **Security**: Zero CVEs in dependencies, all tools have validation
- **Performance**: <100ms overhead per tool invocation
- **Compliance**: Full audit trail for all state mutations
- **Reliability**: 99.9% uptime for MCP server
- **Maintainability**: All security patterns documented in AGENTS.md

---

## Appendix A: MCP Tool Safety Annotations Reference

| Annotation | Type | Description |
|------------|------|-------------|
| `readOnlyHint` | bool | Tool doesn't modify state |
| `destructiveHint` | bool | Tool may destroy data |
| `idempotentHint` | bool | Same input = same output |
| `openWorldHint` | bool | Tool interacts with external systems |

## Appendix B: Security Checklist

- [ ] All inputs validated with Pydantic
- [ ] Phase names whitelisted
- [ ] Tool descriptions sanitized
- [ ] Audit logging enabled
- [ ] Rate limiting configured
- [ ] Transport secured (TLS for HTTP)
- [ ] Dependencies pinned and audited
- [ ] Security annotations on all tools
- [ ] Error messages don't leak internals
- [ ] Timeouts configured for all operations
