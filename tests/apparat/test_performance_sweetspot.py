"""
Performance and sweet-spot benchmark test.
Measures execution latency across grid dimensions (4x4 to 128x128)
to verify performance scaling and throughput balance.
"""

import time

import pytest

from mangrove_platform.apparat.apparat import (
    clamp_handler,
    highlight_handler,
    normalize_handler,
    register_phase_handler,
    scale_handler,
)
from mangrove_platform.apparat.horizontal_texture_processor import HorizontalTextureProcessor
from mangrove_platform.apparat.phase_handlers import (
    combine_handler,
    complete_handler,
    initiate_handler,
    quantize_handler,
)


@pytest.fixture(autouse=True)
def setup_handlers():
    register_phase_handler("initiate", signature={})(initiate_handler)
    register_phase_handler("scale", signature={"factor": float}, param_map=["factor"])(
        scale_handler
    )
    register_phase_handler("normalize", signature={})(normalize_handler)
    register_phase_handler(
        "clamp", signature={"min_val": float, "max_val": float}, param_map=["min_val", "max_val"]
    )(clamp_handler)
    register_phase_handler("quantize", signature={})(quantize_handler)
    register_phase_handler("combine", signature={})(combine_handler)
    register_phase_handler("highlight", signature={})(highlight_handler)
    register_phase_handler("complete", signature={})(complete_handler)


class TestPerformanceSweetSpot:
    """Benchmark suite for finding high-throughput sweet spot grid dimensions."""

    @pytest.mark.parametrize("size", [4, 16, 32, 64, 128])
    def test_grid_scale_performance(self, size: int):
        """Benchmark multi-stage pipeline execution time across scaling dimensions."""
        processor = HorizontalTextureProcessor(size, size)
        pipeline = ["initiate", "scale:1.5", "normalize", "highlight", "complete"]

        start_time = time.perf_counter()
        for phase in pipeline:
            processor.process_phase(phase)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        cell_count = size * size
        us_per_cell = (elapsed_ms * 1000.0) / cell_count

        # Performance assertion: processing per cell must stay under 15 microseconds
        assert us_per_cell < 15.0, (
            f"Latency per cell ({us_per_cell:.2f} µs) exceeded baseline budget for {size}x{size}"
        )
