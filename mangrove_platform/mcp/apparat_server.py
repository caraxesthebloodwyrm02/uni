import logging

from mcp.server.fastmcp import FastMCP  # type: ignore

from mangrove_platform.mcp import apparat_logic
from mangrove_platform.mcp.security import (
    PhaseRequest,
    PipelineRequest,
    _ErrorResult,
    _RateLimitedResult,
    log_tool_invocation,
    rate_limiter,
    safety_annotations,
    validate_request,
)

# Configure root logger so security.log_tool_invocation's INFO entries
# reach the MCP transport's stderr sink (without this, the audit log is
# silently swallowed on a fresh interpreter).
logging.basicConfig(level=logging.INFO)

# Create the MCP server
mcp = FastMCP("Apparat-Server")

# Default grid resolution used by tools that don't take width/height params
# (e.g. list_apparat_hooks, register_apparat_hook). Must match the GridRequest
# default in security.py so the global processor is created with the same
# dimensions callers would otherwise pass.
_DEFAULT_GRID_DIMS = (4, 4)


def _gate(tool_name: str, model_type, params: dict) -> dict:
    """Shared entry gate: rate-limit, then validate. Returns validated params or error payload.

    Every entry through this gate is logged via ``log_tool_invocation``.
    """
    allowed, retry_after_seconds = rate_limiter.allow(tool_name)
    if not allowed:
        result = _RateLimitedResult(
            error="Rate limit exceeded",
            retry_after_seconds=round(retry_after_seconds, 3),
        )
        log_tool_invocation(tool_name, params, "rate_limited", detail=result.error)
        return {
            "status": "error",
            "error": result.error,
            "retry_after_seconds": result.retry_after_seconds,
        }
    result = validate_request(model_type, params)
    # ``result`` is either ``dict`` (success) or ``_ErrorResult`` (failure).
    if isinstance(result, _ErrorResult):
        log_tool_invocation(tool_name, params, "validation_failed", detail=result.error)
        return {"status": "error", "error": result.error}
    return result


@mcp.tool(
    annotations=safety_annotations(
        read_only=True, destructive=False, idempotent=True, open_world=False
    )
)
def check_apparat_health():
    """
    Performs a full SISA bootstrap health check of the Apparat subsystem.
    Returns components status, resolved phases, and any architectural warnings.
    """
    log_tool_invocation("check_apparat_health", {}, "success")
    return apparat_logic.check_apparat_health()


@mcp.tool(
    annotations=safety_annotations(
        read_only=True, destructive=False, idempotent=True, open_world=False
    )
)
def get_apparat_state(width: int = 4, height: int = 4):
    """
    Retrieves the current state of the global Apparat processor,
    including resolution and the last successfully executed phase.

    Args:
        width: Grid width (1-100).
        height: Grid height (1-100).
    """
    from .security import GridRequest

    params = {"width": width, "height": height}
    validated = validate_request(GridRequest, params)
    if isinstance(validated, _ErrorResult):
        log_tool_invocation(
            "get_apparat_state", params, "validation_failed", detail=validated.error
        )
        # Wire-format dict for MCP transport — mirrors the shape _gate would
        # have produced had this tool gone through the gate.
        return {"status": "error", "error": validated.error}
    log_tool_invocation("get_apparat_state", validated, "success")
    return apparat_logic.get_apparat_state(validated["width"], validated["height"])


@mcp.tool(
    annotations=safety_annotations(
        read_only=True, destructive=False, idempotent=True, open_world=False
    )
)
def list_apparat_phases():
    """
    Returns a list of all currently registered phase handlers in the Apparat registry.
    """
    log_tool_invocation("list_apparat_phases", {}, "success")
    return apparat_logic.list_apparat_phases()


@mcp.tool(
    annotations=safety_annotations(
        read_only=False, destructive=False, idempotent=True, open_world=False
    )
)
def run_apparat_phase(phase: str, width: int = 4, height: int = 4):
    """
    Executes a specific Apparat phase processing step.

    Args:
        phase: The phase name (e.g., 'initiate', 'scale:2.0', 'clamp:0.1,0.9').
        width: Grid width (1-100).
        height: Grid height (1-100).
    """
    validated = _gate(
        "run_apparat_phase", PhaseRequest, {"phase": phase, "width": width, "height": height}
    )
    if validated.get("status") == "error":
        return validated
    result = apparat_logic.run_apparat_phase(
        validated["phase"], validated["width"], validated["height"]
    )
    log_tool_invocation("run_apparat_phase", validated, result.get("status", "unknown"))
    return result


@mcp.tool(
    annotations=safety_annotations(
        read_only=False, destructive=False, idempotent=True, open_world=False
    )
)
def run_apparat_pipeline(pipeline: str, width: int = 4, height: int = 4):
    """
    Executes a sequence of Apparat phase processing steps in a single call.

    Args:
        pipeline: A slash-separated sequence of phases (e.g., 'initiate/scale:2.0/complete').
        width: Grid width (1-100).
        height: Grid height (1-100).
    """
    validated = _gate(
        "run_apparat_pipeline",
        PipelineRequest,
        {"pipeline": pipeline, "width": width, "height": height},
    )
    if validated.get("status") == "error":
        return validated
    result = apparat_logic.run_apparat_pipeline(
        validated["pipeline"], validated["width"], validated["height"]
    )
    log_tool_invocation("run_apparat_pipeline", validated, result.get("status", "unknown"))
    return result


@mcp.tool(
    annotations=safety_annotations(
        read_only=False, destructive=False, idempotent=False, open_world=False
    )
)
def register_apparat_hook(hook_type: str, handler_name: str, phase: str | None = None):
    """
    Register a new pre- or post-phase hook into the Apparat processor.
    Used for management, rule enforcement, and custom monitoring.

    Args:
        hook_type: 'pre' or 'post'.
        handler_name: Name of the handler function.
        phase: Optional phase name to bind the hook to.
    """
    from .security import HookRegistrationRequest

    params = {"hook_type": hook_type, "handler_name": handler_name, "phase": phase}
    validated = _gate("register_apparat_hook", HookRegistrationRequest, params)
    if validated.get("status") == "error":
        return validated

    processor = apparat_logic.get_processor(*_DEFAULT_GRID_DIMS)

    # For the MCP stub, we resolve the handler from the processor's
    # internal logic or a predefined set of management la-hooks.
    # In a full version, we would look up the handler in a specialized HookRegistry.

    # Defensive implementation: we only allow registration of la-hooks
    # that are actually definedS in the approved hook whitelist.
    if not apparat_logic.is_approved_hook(handler_name):
        log_tool_invocation(
            "register_apparat_hook",
            validated,
            "error",
            detail=f"Handler {handler_name} is not whitelisted for hook registration",
        )
        return {
            "status": "error",
            "error": f"Handler {handler_name} is not whitelisted for hook registration",
        }

    handler = getattr(processor, handler_name, None)
    if not handler or not callable(handler):
        log_tool_invocation(
            "register_apparat_hook",
            validated,
            "error",
            detail=f"Handler {handler_name} not found on processor",
        )
        return {"status": "error", "error": f"Handler {handler_name} not found on processor"}

    processor.register_hook(validated["hook_type"], validated["phase"], handler)
    log_tool_invocation("register_apparat_hook", validated, "success")
    return {"status": "success", "phase": validated["phase"] or "global", "hook": hook_type}


@mcp.tool(
    annotations=safety_annotations(
        read_only=True, destructive=False, idempotent=True, open_world=False
    )
)
def list_apparat_hooks():
    """
    Lists all registered pre- and post-phase hooks.
    """
    log_tool_invocation("list_apparat_hooks", {}, "success")
    processor = apparat_logic.get_processor(*_DEFAULT_GRID_DIMS)

    return {
        "pre_hooks": {k: [h.__name__ for h in v] for k, v in processor.pre_hooks.items()},
        "post_hooks": {k: [h.__name__ for h in v] for k, v in processor.post_hooks.items()},
        "global_pre": [h.__name__ for h in processor.global_pre_hooks],
        "global_post": [h.__name__ for h in processor.global_post_hooks],
    }


if __name__ == "__main__":
    mcp.run()
