import os
import sys
from typing import Any

# Ensure we are in the mangrove root for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../../"))
sys.path.insert(0, root_dir)

try:
    from apparat.apparat import (
        PHASE_REGISTRY,
        register_phase_handler,
    )
    from apparat.horizontal_texture_processor import HorizontalTextureProcessor
    from apparat.sisa import sisa, to_jsonable
except ImportError as e:
    print(f"Error importing Apparat components: {e}")
    raise e

from mcp.constraints_engine import ConstraintsEngine  # noqa: E402


def initialize_apparat():
    """
    Properly initialize the Apparat subsystem.
    Populates the registry with both built-in and specialized phase handlers.
    """
    # 1. Register specialized handlers from phase_handlers.py
    from mangrove.platform.apparat.phase_handlers import (
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
constraints_engine = ConstraintsEngine(root_dir=os.path.join(root_dir, "mangrove"))

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


# Run initialization on module load
initialize_apparat()
