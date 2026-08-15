"""
Apparat Subsystem

A high-accuracy, type-safe dynamic phase-handler registry for grid-cell processing.
"""

from .api import ApparatValidationError, GridCell, InputProcessOutput, Phase
from .apparat import get_phase_handler, register_phase_handler
from .horizontal_texture_processor import HorizontalTextureProcessor

__all__ = [
    "GridCell",
    "Phase",
    "InputProcessOutput",
    "ApparatValidationError",
    "register_phase_handler",
    "get_phase_handler",
    "HorizontalTextureProcessor",
]

# Register phase handlers from phase_handlers.py
from .phase_handlers import (
    combine_handler,
    complete_handler,
    compliance_baseline_handler,
    initiate_handler,
    quantize_handler,
    render_handler,
)

register_phase_handler("initiate")(initiate_handler)
register_phase_handler("quantize")(quantize_handler)
register_phase_handler("combine")(combine_handler)
register_phase_handler("render")(render_handler)
register_phase_handler("complete")(complete_handler)
register_phase_handler("compliance_baseline")(compliance_baseline_handler)
