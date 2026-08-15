import logging

from mangrove_platform.mcp import apparat_logic
from mangrove_platform.mcp.security import (
    ConstraintSearchRequest,
    GridRequest,
    HookRegistrationRequest,
    PhaseInspectionRequest,
    PhaseRequest,
    PipelineRequest,
    _ErrorResult,
    _RateLimitedResult,
    log_tool_invocation,
    rate_limiter,
    safety_annotations,
    validate_request,
)

# Configure root logger
logging.basicConfig(level=logging.INFO)

try:
    from mcp.server.mcpserver import MCPServer

    mcp = MCPServer("Apparat-Server")
except Exception:
    try:
        from fastmcp import FastMCP  # type: ignore

        mcp = FastMCP("Apparat-Server")
    except Exception:
        from mcp.server.fastmcp import FastMCP  # type: ignore

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
    params = {"hook_type": hook_type, "handler_name": handler_name, "phase": phase}
    validated = _gate("register_apparat_hook", HookRegistrationRequest, params)
    if validated.get("status") == "error":
        return validated

    processor = apparat_logic.get_processor(*_DEFAULT_GRID_DIMS)

    # Defensive implementation: we only allow registration of hooks
    # that are actually defined in the approved hook whitelist.
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


@mcp.tool(
    annotations=safety_annotations(
        read_only=True, destructive=False, idempotent=True, open_world=False
    )
)
def search_constraints(query: str | None = None):
    """
    Searches for systemic constraints, validation rules, regex patterns,
    and operational limits embedded across the Mangrove codebase.

    Args:
        query: Optional search term or regex filter.
    """
    params = {"query": query}
    validated = _gate("search_constraints", ConstraintSearchRequest, params)
    if validated.get("status") == "error":
        return validated
    result = apparat_logic.search_constraints(validated.get("query"))
    log_tool_invocation("search_constraints", validated, "success")
    return {"status": "success", "count": len(result), "constraints": result}


@mcp.tool(
    annotations=safety_annotations(
        read_only=True, destructive=False, idempotent=True, open_world=False
    )
)
def render_apparat_matrix(width: int = 4, height: int = 4):
    """
    Renders the current spatial grid state as formatted 2D row matrices and ASCII textures.

    Args:
        width: Grid width (1-100).
        height: Grid height (1-100).
    """
    params = {"width": width, "height": height}
    validated = validate_request(GridRequest, params)
    if isinstance(validated, _ErrorResult):
        log_tool_invocation(
            "render_apparat_matrix", params, "validation_failed", detail=validated.error
        )
        return {"status": "error", "error": validated.error}
    result = apparat_logic.render_apparat_matrix(validated["width"], validated["height"])
    log_tool_invocation("render_apparat_matrix", validated, "success")
    return result


@mcp.tool(
    annotations=safety_annotations(
        read_only=True, destructive=False, idempotent=True, open_world=False
    )
)
def get_phase_signature(phase: str):
    """
    Inspects registration metadata, parameter types, positional mapping,
    and docstrings for a specific registered Apparat phase handler.

    Args:
        phase: Phase identifier (e.g., 'scale', 'clamp', 'highlight').
    """
    params = {"phase": phase}
    validated = _gate("get_phase_signature", PhaseInspectionRequest, params)
    if validated.get("status") == "error":
        return validated
    result = apparat_logic.get_phase_signature_info(validated["phase"])
    log_tool_invocation("get_phase_signature", validated, result.get("status", "unknown"))
    return result


@mcp.tool(
    annotations=safety_annotations(
        read_only=False, destructive=True, idempotent=True, open_world=False
    )
)
def reset_apparat_processor(width: int = 4, height: int = 4):
    """
    Resets the global Apparat processor canvas to an empty initial state with the specified dimensions.

    Args:
        width: Grid width (1-100).
        height: Grid height (1-100).
    """
    params = {"width": width, "height": height}
    validated = _gate("reset_apparat_processor", GridRequest, params)
    if validated.get("status") == "error":
        return validated
    result = apparat_logic.reset_apparat_processor(validated["width"], validated["height"])
    log_tool_invocation("reset_apparat_processor", validated, "success")
    return result


if __name__ == "__main__":
    mcp.run()
