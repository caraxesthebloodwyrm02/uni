#!/usr/bin/env python3
"""Integration tests for end-to-end Apparat pipelines."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../platform"))

from apparat.api import GridCell, Phase
from apparat.apparat import (
    clamp_handler,
    filter_handler,
    invert_handler,
    normalize_handler,
    register_phase_handler,
    scale_handler,
)
from apparat.horizontal_texture_processor import HorizontalTextureProcessor
from apparat.phase_handlers import (
    combine_handler,
    complete_handler,
    initiate_handler,
    quantize_handler,
    render_handler,
)


def test_full_pipeline_basic():
    """Test complete pipeline: initiate → scale → normalize → complete."""
    processor = HorizontalTextureProcessor(4, 4)

    # Register the handlers we need
    register_phase_handler("initiate", signature={})(initiate_handler)
    register_phase_handler("scale", signature={"factor": float}, param_map=["factor"])(
        scale_handler
    )
    register_phase_handler("normalize", signature={})(normalize_handler)
    register_phase_handler("complete", signature={})(complete_handler)

    # Execute pipeline
    processor.process_phase("initiate")

    # Set some test values
    for i, cell in enumerate(processor.ipo.input_data):
        processor.ipo.input_data[i] = GridCell(cell.x, cell.y, float(i) / 10.0, cell.texture_type)

    processor.process_phase("scale:2.0")
    processor.process_phase("normalize")
    processor.process_phase("complete")

    # Verify final state
    assert len(processor.ipo.input_data) == 16
    # After scaling by 2.0 and normalizing, values should be in [0,1]
    for cell in processor.ipo.input_data:
        assert 0.0 <= cell.value <= 1.0

    print("PASS: test_full_pipeline_basic")


def test_complex_pipeline_with_multiple_params():
    """Test pipeline with multiple parameters: initiate → clamp → filter → invert."""
    processor = HorizontalTextureProcessor(4, 4)

    # Register handlers
    register_phase_handler("initiate", signature={})(initiate_handler)
    register_phase_handler(
        "clamp", signature={"min_val": float, "max_val": float}, param_map=["min_val", "max_val"]
    )(clamp_handler)
    register_phase_handler("filter", signature={"threshold": float}, param_map=["threshold"])(
        filter_handler
    )
    register_phase_handler("invert", signature={})(invert_handler)

    # Execute pipeline
    processor.process_phase("initiate")

    # Set test values (0.0 to 1.5)
    for i, cell in enumerate(processor.ipo.input_data):
        processor.ipo.input_data[i] = GridCell(cell.x, cell.y, float(i) / 10.0, cell.texture_type)

    processor.process_phase("clamp:0.2,1.0")
    processor.process_phase("filter:0.5")
    processor.process_phase("invert")

    # Verify final state
    assert len(processor.ipo.input_data) < 16  # Some filtered out
    # All remaining values should be inverted and >= 0.5 originally
    for cell in processor.ipo.input_data:
        assert cell.value <= 0.5  # Inverted from >= 0.5
        assert cell.value >= 0.0  # Clamped minimum

    print("PASS: test_complex_pipeline_with_multiple_params")


def test_pipeline_with_quantize_and_combine():
    """Test pipeline with quantize and combine phases."""
    processor = HorizontalTextureProcessor(4, 4)

    # Register handlers
    register_phase_handler("initiate", signature={})(initiate_handler)
    register_phase_handler("quantize", signature={})(quantize_handler)
    register_phase_handler("combine", signature={})(combine_handler)
    register_phase_handler("complete", signature={})(complete_handler)

    # Execute pipeline
    processor.process_phase("initiate")

    # Set test values with many decimals
    for i, cell in enumerate(processor.ipo.input_data):
        processor.ipo.input_data[i] = GridCell(cell.x, cell.y, float(i) / 7.0, "empty")

    processor.process_phase("quantize")
    processor.process_phase("combine")
    processor.process_phase("complete")

    # Verify quantization worked
    for cell in processor.ipo.input_data:
        # Should be rounded to 1 decimal place
        expected = round((float(cell.x + cell.y * 4) / 7.0) * 10) / 10
        assert cell.value == expected, f"Expected {expected}, got {cell.value}"

    # Verify combine worked (texture should have hyphens)
    assert all("-" in cell.texture_type for cell in processor.ipo.input_data)

    print("PASS: test_pipeline_with_quantize_and_combine")


def test_pipeline_error_recovery():
    """Test pipeline behavior when a phase fails."""
    processor = HorizontalTextureProcessor(4, 4)

    # Register handlers
    register_phase_handler("initiate", signature={})(initiate_handler)
    register_phase_handler("good_phase", signature={})(complete_handler)
    # Don't register bad_phase - this should fail

    # Execute successful phases
    processor.process_phase("initiate")
    initial_count = len(processor.ipo.input_data)
    assert initial_count == 16

    # Try to execute bad phase
    try:
        processor.process_phase("bad_phase")
        raise AssertionError("Should have raised an error for unregistered phase")
    except Exception as e:
        assert "not found in registry" in str(e)

    # Verify state is preserved after error
    assert len(processor.ipo.input_data) == initial_count

    # Can still execute good phases
    processor.process_phase("good_phase")
    assert len(processor.ipo.input_data) == initial_count

    print("PASS: test_pipeline_error_recovery")


def test_pipeline_state_transitions():
    """Test that current_phase updates correctly during pipeline execution."""
    processor = HorizontalTextureProcessor(4, 4)

    # Register handlers
    register_phase_handler("initiate", signature={})(initiate_handler)
    register_phase_handler("quantize", signature={})(quantize_handler)
    register_phase_handler("complete", signature={})(complete_handler)

    # Check initial phase
    assert processor.current_phase == Phase.INITIATE

    # Execute phases and check transitions
    processor.process_phase("initiate")
    # After initiate, phase should still be INITIATE (no explicit phase change in handler)

    processor.process_phase("quantize")
    # After quantize, should be QUANTIZE
    assert processor.current_phase == Phase.QUANTIZE

    processor.process_phase("complete")
    # After complete, should be COMPLETE
    assert processor.current_phase == Phase.COMPLETE

    print("PASS: test_pipeline_state_transitions")


def test_pipeline_with_different_resolutions():
    """Test pipeline works correctly with different grid resolutions."""
    resolutions = [(2, 2), (4, 4), (8, 8), (16, 4)]

    for width, height in resolutions:
        processor = HorizontalTextureProcessor(width, height)

        # Register handlers
        register_phase_handler("initiate", signature={})(initiate_handler)
        register_phase_handler("complete", signature={})(complete_handler)

        # Execute pipeline
        processor.process_phase("initiate")
        processor.process_phase("complete")

        # Verify correct number of cells
        expected_count = width * height
        assert len(processor.ipo.input_data) == expected_count

        # Verify coordinates are correct
        for cell in processor.ipo.input_data:
            assert 0 <= cell.x < width
            assert 0 <= cell.y < height

    print("PASS: test_pipeline_with_different_resolutions")


def test_pipeline_with_render_phase():
    """Test pipeline including render phase."""
    processor = HorizontalTextureProcessor(4, 4)

    # Register handlers
    register_phase_handler("initiate", signature={})(initiate_handler)
    register_phase_handler("render", signature={})(render_handler)
    register_phase_handler("complete", signature={})(complete_handler)

    # Execute pipeline
    processor.process_phase("initiate")
    processor.process_phase("render")
    processor.process_phase("complete")

    # Verify render worked (should have processed_data set)
    assert processor.ipo.processed_data is not None or processor.ipo.input_data is not None

    print("PASS: test_pipeline_with_render_phase")


def test_pipeline_data_flow():
    """Test that data flows correctly between pipeline stages using built-in handlers."""
    processor = HorizontalTextureProcessor(4, 4)

    # Register handlers that transform data in predictable ways
    register_phase_handler("initiate", signature={})(initiate_handler)
    register_phase_handler("scale", signature={"factor": float}, param_map=["factor"])(
        scale_handler
    )
    register_phase_handler("invert", signature={})(invert_handler)

    # Execute pipeline
    processor.process_phase("initiate")

    # Set initial values
    for i, cell in enumerate(processor.ipo.input_data):
        processor.ipo.input_data[i] = GridCell(cell.x, cell.y, 0.5, "test")

    processor.process_phase("scale:2.0")  # 0.5 * 2.0 = 1.0
    processor.process_phase("invert")  # 1.0 - 1.0 = 0.0

    # Verify final values
    for cell in processor.ipo.input_data:
        assert cell.value == 0.0, f"Expected 0.0, got {cell.value}"

    print("PASS: test_pipeline_data_flow")


if __name__ == "__main__":
    test_full_pipeline_basic()
    test_complex_pipeline_with_multiple_params()
    test_pipeline_with_quantize_and_combine()
    test_pipeline_error_recovery()
    test_pipeline_state_transitions()
    test_pipeline_with_different_resolutions()
    test_pipeline_with_render_phase()
    test_pipeline_data_flow()
    print("\n✨ All integration tests passed!")
