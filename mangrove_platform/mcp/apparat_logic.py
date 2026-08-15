# Determine the mangrove root from this file's location (mangrove_platform/mcp/apparat_logic.py).
import os
from typing import Any

from mangrove_platform.apparat.api import ApparatValidationError
from mangrove_platform.apparat.apparat import (
    PHASE_REGISTRY,
    register_phase_handler,
)
from mangrove_platform.apparat.horizontal_texture_processor import HorizontalTextureProcessor
from mangrove_platform.apparat.phase_validation import validate_pipeline
from mangrove_platform.apparat.sisa import sisa, to_jsonable
from mangrove_platform.mcp.constraints_engine import ConstraintsEngine

_APPARAT_LOGIC_DIR = os.path.dirname(os.path.abspath(__file__))
mangrove_dir = os.path.abspath(os.path.join(_APPARAT_LOGIC_DIR, "../.."))


def initialize_apparat():
    """
    Properly initialize the Apparat subsystem.
    Populates the registry with both built-in and specialized phase handlers.
    """
    # 1. Register specialized handlers from phase_handlers.py
    from mangrove_platform.apparat.phase_handlers import (
        combine_handler,
        complete_handler,
        compliance_baseline_handler,
        initiate_handler,
        quantize_handler,
        render_handler,
    )

    # Map handler functions to their phase names with associated signatures
    specialized_handlers = {
        "initiate": (initiate_handler, {}),
        "quantize": (quantize_handler, {}),
        "combine": (combine_handler, {}),
        "render": (render_handler, {}),
        "complete": (complete_handler, {}),
        "compliance_baseline": (compliance_baseline_handler, {}),
    }

    for name, (handler, signature) in specialized_handlers.items():
        register_phase_handler(name, signature=signature)(handler)


# Initialize the constraints engine
constraints_engine = ConstraintsEngine(root_dir=mangrove_dir)

# Global processor to maintain state across MCP tool calls
_GLOBAL_PROCESSOR: HorizontalTextureProcessor | None = None


def get_processor(width: int, height: int) -> HorizontalTextureProcessor:
    """Get or create the global processor instance."""
    global _GLOBAL_PROCESSOR
    if _GLOBAL_PROCESSOR is None or _GLOBAL_PROCESSOR.resolution != (width, height):
        _GLOBAL_PROCESSOR = HorizontalTextureProcessor(width, height)
    return _GLOBAL_PROCESSOR


def get_registry():
    """Retrieve the active phase handler registry."""
    return PHASE_REGISTRY


def check_apparat_health() -> dict[str, Any]:
    """
    Performs a full SISA bootstrap check of the Apparat subsystem.
    Returns the health state including loaded components, resolved phases, and warnings.
    """
    state = sisa()
    return to_jsonable(state)


def list_apparat_phases() -> list[str]:
    """
    Returns a list of all currently registered phase handlers in the Apparat registry.
    """
    return list(get_registry().keys())


def get_apparat_state(width: int = 4, height: int = 4) -> dict[str, Any]:
    """
    Retrieve the current state of the global Apparat processor.
    """
    processor = get_processor(width, height)
    current_phase = processor.current_phase
    # If current_phase is an Enum, use its value. Otherwise, use it as is.
    phase_name = current_phase.value if hasattr(current_phase, "value") else str(current_phase)

    return {
        "resolution": processor.resolution,
        "source_id": processor.source_id,
        "current_phase": phase_name,
        "cell_count": len(processor.ipo.input_data),
    }


def run_apparat_pipeline(pipeline_spec: str, width: int = 4, height: int = 4) -> dict[str, Any]:
    """
    Executes a sequence of Apparat phases.
    Format: 'phase1/phase2:arg1,arg2/phase3'
    """
    try:
        validate_pipeline(pipeline_spec)
    except ApparatValidationError as e:
        return {"status": "error", "error": str(e)}

    phases = [p for p in pipeline_spec.split("/") if p]
    if not phases:
        return {"status": "error", "error": "Empty pipeline specification"}

    executed_phases = []
    last_result = []

    for phase in phases:
        res = run_apparat_phase(phase, width, height)
        if res["status"] == "error":
            return {
                "status": "error",
                "failed_phase": phase,
                "error": res["error"],
                "executed_phases": executed_phases,
            }
        executed_phases.append(phase)
        last_result = res.get("result", [])

    return {"status": "success", "executed_phases": executed_phases, "result": last_result}


def run_apparat_phase(phase: str, width: int = 4, height: int = 4) -> dict[str, Any]:
    """
    Executes a specific Apparat phase processing step.
    Maintains state in a global processor across calls.
    """
    try:
        processor = get_processor(width, height)
        result_grid = processor.process_phase(phase)

        serialized_result = []
        for cell in result_grid:
            serialized_result.append(
                {"x": cell.x, "y": cell.y, "value": cell.value, "texture_type": cell.texture_type}
            )

        return {"status": "success", "phase": phase, "result": serialized_result}
    except Exception as e:
        return {"status": "error", "phase": phase, "error": str(e)}


def search_constraints(query: str | None = None) -> list[dict[str, Any]]:
    """
    Locates systemic constraints, rules, and limits embedded in the codebase.
    """
    return constraints_engine.search(query)


def is_approved_hook(handler_name: str) -> bool:
    """
    Validates if a given handler name is in the whitelist of approved Apparat hooks.
    This prevents arbitrary code execution via MCP hook registration.
    """
    approved_hooks = {
        "_system_baseline_update",
        "_system_audit_log",
        "_post_scale",
        "_post_render",
        "_post_complete",
    }
    return handler_name in approved_hooks


def get_gemini_tool_declarations() -> list[dict[str, Any]]:
    """Returns Gemini Interactions / Live API function declarations for Apparat."""
    return [
        {
            "function_declarations": [
                {
                    "name": "list_apparat_phases",
                    "description": "Lists all registered phase handlers in Mangrove Apparat.",
                    "parameters": {"type": "OBJECT", "properties": {}},
                },
                {
                    "name": "run_apparat_phase",
                    "description": "Executes a single processing phase in the Apparat pipeline.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "phase": {
                                "type": "STRING",
                                "description": "Phase identifier (e.g. initiate, normalize, scale:2.0)",
                            },
                            "width": {"type": "INTEGER", "description": "Grid width", "default": 4},
                            "height": {
                                "type": "INTEGER",
                                "description": "Grid height",
                                "default": 4,
                            },
                        },
                        "required": ["phase"],
                    },
                },
                {
                    "name": "run_apparat_pipeline",
                    "description": "Executes a sequence of Apparat phases separated by slashes.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "pipeline": {
                                "type": "STRING",
                                "description": "Pipeline specification (e.g. 'initiate/scale:2.0/complete')",
                            },
                            "width": {"type": "INTEGER", "description": "Grid width", "default": 4},
                            "height": {
                                "type": "INTEGER",
                                "description": "Grid height",
                                "default": 4,
                            },
                        },
                        "required": ["pipeline"],
                    },
                },
                {
                    "name": "check_apparat_health",
                    "description": "Performs a full SISA bootstrap check of the Apparat subsystem.",
                    "parameters": {"type": "OBJECT", "properties": {}},
                },
            ]
        }
    ]


def dispatch_gemini_tool_call(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Dispatches a Gemini function tool call to the corresponding Apparat handler."""
    if tool_name == "list_apparat_phases":
        return {"phases": list_apparat_phases()}
    elif tool_name == "run_apparat_phase":
        return run_apparat_phase(
            phase=args.get("phase", ""),
            width=int(args.get("width", 4)),
            height=int(args.get("height", 4)),
        )
    elif tool_name == "run_apparat_pipeline":
        return run_apparat_pipeline(
            pipeline_spec=args.get("pipeline", ""),
            width=int(args.get("width", 4)),
            height=int(args.get("height", 4)),
        )
    elif tool_name == "check_apparat_health":
        return check_apparat_health()
    else:
        return {"status": "error", "error": f"Unknown tool: {tool_name}"}


# Run initialization on module load
initialize_apparat()
