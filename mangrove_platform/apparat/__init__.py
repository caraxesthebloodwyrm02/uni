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
