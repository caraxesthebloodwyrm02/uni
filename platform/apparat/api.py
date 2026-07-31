from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

# --- Base Types ---


class ApparatValidationError(Exception):
    """Exception raised when phase parameter validation fails."""

    pass


# Mapping of positional arguments to named keys for specific phases
# Example: 'scale:2.0' -> {'factor': 2.0}
type PhaseParams = dict[str, Any]

# A signature defines the required parameters and their expected types for a phase.
# Example: {"factor": float}
type PhaseSignature = dict[str, type]


class Phase(Enum):
    """Processing phases for forward slash separation"""

    INITIATE = "initiate"
    QUANTIZE = "quantize"
    COMBINE = "combine"
    RENDER = "render"
    NORMALIZE = "normalize"
    SCALE = "scale"
    CLAMP = "clamp"
    FILTER = "filter"
    INVERT = "invert"
    COMPLETE = "complete"
    HIGHLIGHT = "highlight"
    COMPLIANCE_BASELINE = "compliance_baseline"
    VALIDATE_ACCELERATION = "validate_acceleration"


@dataclass(frozen=True)
class GridCell:
    """
    Single grid cell for block processing.
    Frozen to ensure high-accuracy I/O and prevent implicit state mutation.
    """

    x: int
    y: int
    value: float
    texture_type: str

    def read(self) -> float:
        """Read cell value - complete by read."""
        return self.value


@dataclass
class InputProcessOutput:
    """
    Formalized I/O bridge for phase transitions.
    Manages the current state of the pipeline.
    """

    input_data: list[GridCell] = field(default_factory=list)
    processed_data: list[GridCell] | None = None
    output_data: list[GridCell] | None = None
    compliance_root: str | None = None
    compliance_artifacts: list[tuple[Any, str, int]] | None = None


@dataclass
class ComputationalQuantizationMatrix:
    """Computational Quantization Matrix for spatial processing."""

    matrix: list[list[float]]
    resolution: tuple[int, int]

    def __init__(self, width: int, height: int):
        self.resolution = (width, height)
        self.matrix = [[0.0 for _ in range(width)] for _ in range(height)]

    def set_cell(self, x: int, y: int, value: float):
        if 0 <= x < self.resolution[0] and 0 <= y < self.resolution[1]:
            self.matrix[y][x] = value

    def get_cell(self, x: int, y: int) -> float:
        if 0 <= x < self.resolution[0] and 0 <= y < self.resolution[1]:
            return self.matrix[y][x]
        return 0.0

    def read_row(self, y: int) -> list[float]:
        if 0 <= y < self.resolution[1]:
            return self.matrix[y]
        return []


class SpatialRender:
    """Spatial Render for acoustic/natural visualization."""

    def __init__(self, matrix: ComputationalQuantizationMatrix):
        self.matrix = matrix
        self.render_output: list[list[float]] = []

    def render(self) -> list[list[float]]:
        self.render_output = self.matrix.matrix
        return self.render_output

    def read_render(self) -> list[list[float]]:
        return self.render_output


# --- Interfaces (Protocols) ---


@runtime_checkable
class IProcessor(Protocol):
    """
    Interface for a texture processor.
    Guarantees access to the state and resolution needed by phase handlers.
    """

    resolution: tuple[int, int]
    source_id: str  # Foundational ID for source-aware processing
    ipo: InputProcessOutput
    matrix: ComputationalQuantizationMatrix
    generator: Any  # Needed for combine_handler


class PhaseHandler(Protocol):
    """
    Strict call signature for all Apparat phase handlers.
    """

    def __call__(self, processor: IProcessor, params: PhaseParams) -> list[GridCell]: ...
