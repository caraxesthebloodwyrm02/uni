"""Security layer for the Mangrove MCP server.

Provides input validation, rate limiting, and audit logging for all tool
invocations.  Kept intentionally small: validation happens at the tool entry
point, logging captures invocation metadata only (never full grid data).
"""

from __future__ import annotations

import logging
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from time import monotonic

from pydantic import BaseModel, Field, field_validator

from mangrove_platform.apparat.phase_validation import (
    ALLOWED_PHASES,  # noqa: F401  re-exported for backward-compat (docs/usage.md)
    PHASE_ARG_PATTERN,
    PIPELINE_PATTERN,
    parse_phase_syntax,
    validate_pipeline,
)

logger = logging.getLogger("mangrove.mcp.security")


@dataclass(frozen=True)
class _ErrorResult:
    """Internal base for failure results returned by ``_gate`` and ``validate_request``.

    The leading-underscore name marks this as a private internal type (not part
    of the MCP wire schema). Callers use ``isinstance(...)`` discrimination
    rather than string status matching — see :class:`_RateLimitedResult` and
    :class:`_ValidationFailedResult`. The MCP wire-format dict is built
    explicitly in ``_gate``; the dataclass shape is independent of the wire
    shape so future internal-only fields can be added without breaking the
    transport contract.
    """

    error: str


@dataclass(frozen=True)
class _RateLimitedResult(_ErrorResult):
    """``_gate`` rejected the call via the rate limiter.

    Carries the AWS-style full-jitter retry hint (``retry_after_seconds``) so
    the MCP caller can back off without re-issuing the request immediately.
    """

    retry_after_seconds: float


@dataclass(frozen=True)
class _ValidationFailedResult(_ErrorResult):
    """``validate_request`` rejected the call via Pydantic validation."""


class GridRequest(BaseModel):
    """Shared width/height parameters for grid-processing tools."""

    width: int = Field(4, ge=1, le=100, description="Grid width (1-100).")
    height: int = Field(4, ge=1, le=100, description="Grid height (1-100).")


class PhaseRequest(GridRequest):
    """Request for a single phase invocation."""

    phase: str = Field(..., pattern=PHASE_ARG_PATTERN, description="Phase name.")

    @field_validator("phase")
    @classmethod
    def validate_phase_name(cls, v: str) -> str:
        parse_phase_syntax(v)
        return v


class PipelineRequest(GridRequest):
    """Request for a slash-separated phase pipeline."""

    pipeline: str = Field(
        ...,
        pattern=PIPELINE_PATTERN,
        description="Slash-separated phase sequence.",
    )

    @field_validator("pipeline")
    @classmethod
    def validate_pipeline(cls, v: str) -> str:
        validate_pipeline(v)
        return v


class HookRegistrationRequest(BaseModel):
    """Request to register a new Apparat hook."""

    hook_type: str = Field(..., pattern=r"^(pre|post)$", description="Hook type: 'pre' or 'post'.")
    phase: str | None = Field(None, description="Phase name. If omitted, hook is global.")
    handler_name: str = Field(..., description="Name of the handler function to use.")


class RateLimiter:
    """Fixed-window, in-memory rate limiter keyed by tool name.

    On rejection, ``allow`` returns a ``retry_after_seconds`` hint computed
    via **full-jitter exponential backoff** (the AWS-recommended formula):

        retry_after = uniform(0, min(cap, base * 2 ** consecutive_failures))

    This is the *suggested wait time for the caller* — the server does not
    itself sleep. The caller propagates it to clients (e.g. as an MCP
    error payload's ``retry_after_seconds`` field) so they can honour it.

    Defaults: ``base=0.5s``, ``cap=30s``. With 6 consecutive rejections the
    cap is hit and the upper bound plateaus at 30s.
    """

    BASE_DELAY_SECONDS = 0.5
    MAX_DELAY_SECONDS = 30.0

    def __init__(self, max_calls: int = 100, window_seconds: int = 60) -> None:
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._calls: dict[str, list[float]] = defaultdict(list)
        self._consecutive_rejections: dict[str, int] = defaultdict(int)

    def allow(self, tool_name: str) -> tuple[bool, float]:
        """Record an attempt and return (allowed, retry_after_seconds).

        On success, ``retry_after_seconds`` is ``0.0`` and the rejection
        counter for ``tool_name`` is reset.
        """
        now = monotonic()
        # Drop entries that fell out of the window.
        self._calls[tool_name] = [
            t for t in self._calls[tool_name] if now - t < self.window_seconds
        ]
        if len(self._calls[tool_name]) >= self.max_calls:
            self._consecutive_rejections[tool_name] += 1
            attempt = self._consecutive_rejections[tool_name]
            upper = min(self.MAX_DELAY_SECONDS, self.BASE_DELAY_SECONDS * (2**attempt))
            return False, random.uniform(0.0, upper)  # noqa: S311
        self._calls[tool_name].append(now)
        self._consecutive_rejections[tool_name] = 0
        return True, 0.0


# Shared limiter instance for the server process.
rate_limiter = RateLimiter()


class ToolSafety(Enum):
    """Safety annotations for tool registrations.

    Mirrors the MCP tool-annotation vocabulary so clients can make informed
    trust decisions without executing a tool.
    """

    READ_ONLY = "readOnlyHint"
    DESTRUCTIVE = "destructiveHint"
    IDEMPOTENT = "idempotentHint"
    OPEN_WORLD = "openWorldHint"


def safety_annotations(
    *, read_only: bool, destructive: bool, idempotent: bool, open_world: bool
) -> dict:
    """Build an MCP annotations dict from explicit safety flags."""
    return {
        ToolSafety.READ_ONLY.value: read_only,
        ToolSafety.DESTRUCTIVE.value: destructive,
        ToolSafety.IDEMPOTENT.value: idempotent,
        ToolSafety.OPEN_WORLD.value: open_world,
    }


def log_tool_invocation(tool_name: str, params: dict, status: str, detail: str = "") -> None:
    """Append a structured audit entry for a tool invocation."""
    entry = {
        "event": "mcp.tool_invocation",
        "tool": tool_name,
        "params": params,
        "status": status,
        "detail": detail,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    logger.info(entry["event"], extra=entry)


def validate_request(model_type: type[BaseModel], params: dict) -> dict | _ValidationFailedResult:
    """Validate raw tool parameters against a Pydantic model.

    Returns a dict on success (the Pydantic model's ``model_dump()``) and a
    :class:`_ValidationFailedResult` on failure. The two result shapes are
    deliberately heterogeneous so callers can use ``isinstance(...)`` for
    exhaustive discrimination.
    """
    try:
        return model_type.model_validate(params).model_dump()
    except Exception as exc:
        errors = getattr(exc, "errors", lambda: None)()
        detail = errors if errors else str(exc)
        return _ValidationFailedResult(error=f"Validation failed: {detail}")
