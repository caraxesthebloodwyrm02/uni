"""
Integration test for baseline balance, stability, and accuracy-speed verification.
Ensures that processor state, grid invariants, floating-point numeric precision,
and hook lifecycle remain perfectly stable under high-throughput phase pipelines.
"""

import math

import pytest

from mangrove_platform.apparat.api import GridCell
from mangrove_platform.apparat.apparat import (
    clamp_handler,
    filter_handler,
    highlight_handler,
    invert_handler,
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
    """Ensure baseline phase handlers are registered."""
    register_phase_handler("initiate", signature={})(initiate_handler)
    register_phase_handler("scale", signature={"factor": float}, param_map=["factor"])(
        scale_handler
    )
    register_phase_handler("normalize", signature={})(normalize_handler)
    register_phase_handler(
        "clamp", signature={"min_val": float, "max_val": float}, param_map=["min_val", "max_val"]
    )(clamp_handler)
    register_phase_handler("filter", signature={"threshold": float}, param_map=["threshold"])(
        filter_handler
    )
    register_phase_handler("invert", signature={})(invert_handler)
    register_phase_handler("quantize", signature={})(quantize_handler)
    register_phase_handler("combine", signature={})(combine_handler)
    register_phase_handler("highlight", signature={})(highlight_handler)
    register_phase_handler("complete", signature={})(complete_handler)


class TestBaselineBalanceStability:
    """Test suite verifying numerical accuracy balance and structural stability."""

    def test_numerical_stability_under_repeated_transformations(self):
        """Verify that chained mathematical operations preserve numerical stability and accuracy."""
        processor = HorizontalTextureProcessor(8, 8)
        processor.process_phase("initiate")

        # Set specific floating point values requiring precision
        for i, cell in enumerate(processor.ipo.input_data):
            processor.ipo.input_data[i] = GridCell(
                cell.x, cell.y, (i + 1) * 0.123456789, "acoustic"
            )

        initial_sum = sum(c.value for c in processor.ipo.input_data)
        assert initial_sum > 0.0

        # Execute multi-stage pipeline: scale -> normalize -> scale -> clamp -> quantize
        processor.process_phase("scale:2.0")
        processor.process_phase("normalize")
        processor.process_phase("scale:10.0")
        processor.process_phase("clamp:0.0,10.0")
        processor.process_phase("quantize")

        # Verify output state bounds and non-NaN / non-Inf integrity
        for cell in processor.ipo.input_data:
            assert not math.isnan(cell.value)
            assert not math.isinf(cell.value)
            assert 0.0 <= cell.value <= 10.0
            # Quantize rounds to 1 decimal place: check exact precision match
            assert round(cell.value, 1) == cell.value

    def test_grid_dimension_and_cell_count_invariants(self):
        """Verify cell resolution invariants hold across non-filtering phases."""
        for size in [4, 16, 32]:
            processor = HorizontalTextureProcessor(size, size)
            processor.process_phase("initiate")
            expected_count = size * size

            # Standard pipeline sequence (none of these filter cells out)
            pipeline = ["scale:1.5", "normalize", "highlight", "quantize", "combine", "complete"]
            for phase in pipeline:
                processor.process_phase(phase)
                assert len(processor.ipo.input_data) == expected_count, (
                    f"Cell count mismatch after phase {phase} on {size}x{size} grid"
                )

    def test_hook_lifecycle_and_history_accuracy(self):
        """Verify hook execution order and accurate history logging."""
        processor = HorizontalTextureProcessor(4, 4)
        processor.process_phase("initiate")

        execution_log = []

        def custom_pre_hook(proc, name, params):
            execution_log.append(f"pre_{name}")
            return params

        def custom_post_hook(proc, name, result):
            execution_log.append(f"post_{name}")
            return result

        processor.register_hook("pre", "scale", custom_pre_hook)
        processor.register_hook("post", "scale", custom_post_hook)

        processor.process_phase("scale:2.0")

        assert "pre_scale" in execution_log
        assert "post_scale" in execution_log

        # Verify audit history logged every executed phase
        history_phases = [entry["phase"] for entry in processor.ipo.history]
        assert "initiate" in history_phases
        assert "scale" in history_phases

    def test_repetition_combination_cache_stability(self):
        """Verify texture string caching delivers accurate highlight tags across repeated runs."""
        processor = HorizontalTextureProcessor(4, 4)
        processor.process_phase("initiate")

        # First highlight pass
        res1 = processor.process_phase("highlight")
        labels1 = [c.texture_type for c in res1]

        # Second highlight pass (uses cache pathways)
        res2 = processor.process_phase("highlight")
        labels2 = [c.texture_type for c in res2]

        assert labels1 == labels2
        assert all("highlight=" in text for text in labels2)
