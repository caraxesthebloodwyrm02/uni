"""
Apparat - Dynamic Phase Processing Registry
This module provides a registry for phase handlers to be used by
horizontal_texture_processor.py and other components.
"""

from .api import ApparatValidationError, PhaseHandler, PhaseSignature

# The registry maps phase names (strings) to a tuple of (handler, signature, param_map)
# This ensures that the dispatcher can validate parameters and map positional args.
PHASE_REGISTRY: dict[str, tuple[PhaseHandler, PhaseSignature | None, list[str] | None]] = {}


def register_phase_handler(
    phase_name: str, signature: PhaseSignature | None = None, param_map: list[str] | None = None
):
    """
    Decorator to register a phase handler with an optional parameter signature and positional map.

    Args:
        phase_name: The name of the phase to register.
        signature: A dictionary mapping parameter names to expected types.
        param_map: A list of keys to map positional arguments to.
    """

    def decorator(func: PhaseHandler) -> PhaseHandler:
        PHASE_REGISTRY[phase_name] = (func, signature, param_map)
        return func

    return decorator


def get_phase_handler(phase_name: str) -> PhaseHandler | None:
    """Retrieve a registered handler for a given phase."""
    entry = PHASE_REGISTRY.get(phase_name)
    return entry[0] if entry else None


def get_phase_signature(phase_name: str) -> PhaseSignature | None:
    """Retrieve the parameter signature for a given phase."""
    entry = PHASE_REGISTRY.get(phase_name)
    return entry[1] if entry else None


def get_phase_param_map(phase_name: str) -> list[str] | None:
    """Retrieve the positional parameter map for a given phase."""
    entry = PHASE_REGISTRY.get(phase_name)
    return entry[2] if entry else None


def list_registered_phases() -> list[str]:
    """Return a list of all phase names with registered handlers."""
    return list(PHASE_REGISTRY.keys())


# --- Built-in Handlers ---


def normalize_handler(processor, params):
    """Normalize cell values to a [0, 1] range."""
    from .api import GridCell

    if not processor.ipo.input_data:
        return []
    values = [cell.value for cell in processor.ipo.input_data]
    min_val, max_val = min(values), max(values)
    if min_val == max_val:
        normalized = [
            GridCell(cell.x, cell.y, 0.5, cell.texture_type) for cell in processor.ipo.input_data
        ]
    else:
        normalized = [
            GridCell(
                cell.x, cell.y, (cell.value - min_val) / (max_val - min_val), cell.texture_type
            )
            for cell in processor.ipo.input_data
        ]
    processor.ipo.input_data = normalized
    return normalized


def scale_handler(processor, params):
    """Scale cell values by a factor."""
    from .api import GridCell

    factor = params.get("factor", 2.0)
    if not processor.ipo.input_data:
        return []
    scaled = [
        GridCell(cell.x, cell.y, cell.value * factor, cell.texture_type)
        for cell in processor.ipo.input_data
    ]
    processor.ipo.input_data = scaled
    return scaled


def clamp_handler(processor, params):
    """Clamp cell values to a specified range."""
    from .api import GridCell

    min_val = params.get("min_val", 0.0)
    max_val = params.get("max_val", 1.0)
    if not processor.ipo.input_data:
        return []
    clamped = [
        GridCell(cell.x, cell.y, max(min_val, min(max_val, cell.value)), cell.texture_type)
        for cell in processor.ipo.input_data
    ]
    processor.ipo.input_data = clamped
    return clamped


def filter_handler(processor, params):
    """Filter cells by value threshold."""
    threshold = params.get("threshold", 0.5)
    if not processor.ipo.input_data:
        return []
    filtered = [cell for cell in processor.ipo.input_data if cell.value >= threshold]
    processor.ipo.input_data = filtered
    return filtered


def invert_handler(processor, params):
    """Invert cell values (1.0 - value)."""
    from .api import GridCell

    if not processor.ipo.input_data:
        return []
    inverted = [
        GridCell(cell.x, cell.y, 1.0 - cell.value, cell.texture_type)
        for cell in processor.ipo.input_data
    ]
    processor.ipo.input_data = inverted
    return inverted


def highlight_handler(processor, params):
    """Highlight cells by annotating texture_type with markers."""
    from .api import GridCell

    if not getattr(processor, "ipo", None) or not processor.ipo.input_data:
        return []
    articles = {"a", "an", "the"}
    vowels = set("aeiou")
    updated = []
    for cell in processor.ipo.input_data:
        label = (cell.texture_type or "").strip()
        if not label:
            updated.append(cell)
            continue
        first_word = label.split()[0].lower()
        tags = []
        if first_word in articles:
            tags.append("article")
        if first_word and first_word[0] in vowels:
            tags.append("vowel")
        elif first_word:
            tags.append("consonant")
        if tags:
            base = (
                cell.texture_type.split("|highlight=")[0]
                if "|highlight=" in cell.texture_type
                else cell.texture_type
            )
            cell_new = GridCell(cell.x, cell.y, cell.value, f"{base}|highlight={'-'.join(tags)}")
            updated.append(cell_new)
        else:
            updated.append(cell)
    processor.ipo.input_data = updated
    return updated


# Register built-ins with signatures and param maps
register_phase_handler("highlight", signature={})(highlight_handler)
register_phase_handler("normalize", signature={})(normalize_handler)
register_phase_handler("scale", signature={"factor": float}, param_map=["factor"])(scale_handler)
register_phase_handler(
    "clamp", signature={"min_val": float, "max_val": float}, param_map=["min_val", "max_val"]
)(clamp_handler)
register_phase_handler("filter", signature={"threshold": float}, param_map=["threshold"])(
    filter_handler
)
register_phase_handler("invert", signature={})(invert_handler)


def validate_acceleration_handler(processor, params):
    """Verify processing acceleration and normalization baselines."""
    from .src.golding import validate

    try:
        # Perform the baseline normalization check
        norm_res = validate.check_baseline_normalization()
        if not norm_res.success:
            raise ApparatValidationError(f"Baseline normalization failed: {norm_res.message}")

        # Perform the cruise engagement check
        cruise_res = validate.check_cruise_engagement()
        if not cruise_res.success:
            raise ApparatValidationError(f"Cruise engagement failed: {cruise_res.message}")

        # If both pass, return the current input data to signify continuation
        return processor.ipo.input_data
    except Exception as e:
        if isinstance(e, ApparatValidationError):
            raise e
        raise ApparatValidationError(f"Golding validation internal error: {e}") from e


register_phase_handler("validate_acceleration", signature={})(validate_acceleration_handler)
