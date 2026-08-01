#!/usr/bin/env python3
"""Tests for phase_handlers.py - core business logic for Apparat phases."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../mangrove_platform"))

from apparat.api import GridCell
from apparat.horizontal_texture_processor import HorizontalTextureProcessor
from apparat.phase_handlers import (
    combine_handler,
    complete_handler,
    compliance_baseline_handler,
    initiate_handler,
    quantize_handler,
    render_handler,
)


def test_initiate_handler_basic():
    """Test initiate_handler creates empty grid with correct resolution."""
    processor = HorizontalTextureProcessor(4, 3)
    result = initiate_handler(processor, {})

    assert len(result) == 12, f"Expected 12 cells (4x3), got {len(result)}"
    assert all(cell.value == 0.0 for cell in result), "All cells should have value 0.0"
    assert all(cell.texture_type == "empty" for cell in result), (
        "All cells should have texture_type 'empty'"
    )

    # Check coordinate assignment
    for y in range(3):
        for x in range(4):
            idx = y * 4 + x
            assert result[idx].x == x, f"Cell {idx} should have x={x}"
            assert result[idx].y == y, f"Cell {idx} should have y={y}"

    print("PASS: test_initiate_handler_basic")


def test_initiate_handler_different_resolutions():
    """Test initiate_handler with various resolutions."""
    test_cases = [
        (1, 1, 1),
        (2, 2, 4),
        (8, 8, 64),
        (16, 4, 64),
    ]

    for width, height, expected_count in test_cases:
        processor = HorizontalTextureProcessor(width, height)
        result = initiate_handler(processor, {})
        assert len(result) == expected_count, (
            f"Expected {expected_count} cells for {width}x{height}"
        )

    print("PASS: test_initiate_handler_different_resolutions")


def test_quantize_handler_basic():
    """Test quantize_handler rounds values to 1 decimal place."""
    processor = HorizontalTextureProcessor(4, 4)
    # Set up test data with various decimal values
    cells = [
        GridCell(0, 0, 0.123456, "empty"),
        GridCell(1, 0, 1.6789, "empty"),
        GridCell(2, 0, 2.5, "empty"),
        GridCell(3, 0, 3.9999, "empty"),
    ]
    processor.ipo.input_data = cells

    result = quantize_handler(processor, {})

    assert len(result) == 4
    assert result[0].value == 0.1, f"Expected 0.1, got {result[0].value}"
    assert result[1].value == 1.7, f"Expected 1.7, got {result[1].value}"
    assert result[2].value == 2.5, f"Expected 2.5, got {result[2].value}"
    assert result[3].value == 4.0, f"Expected 4.0, got {result[3].value}"

    print("PASS: test_quantize_handler_basic")


def test_quantize_handler_empty_input():
    """Test quantize_handler with empty input."""
    processor = HorizontalTextureProcessor(4, 4)
    processor.ipo.input_data = []

    result = quantize_handler(processor, {})

    assert result == [], "Should return empty list for empty input"

    print("PASS: test_quantize_handler_empty_input")


def test_quantize_handler_preserves_coordinates():
    """Test quantize_handler preserves cell coordinates and texture."""
    processor = HorizontalTextureProcessor(4, 4)
    cells = [
        GridCell(2, 3, 1.2345, "test_texture"),
        GridCell(5, 7, 6.7890, "another_texture"),
    ]
    processor.ipo.input_data = cells

    result = quantize_handler(processor, {})

    assert result[0].x == 2
    assert result[0].y == 3
    assert result[0].texture_type == "test_texture"
    assert result[1].x == 5
    assert result[1].y == 7
    assert result[1].texture_type == "another_texture"

    print("PASS: test_quantize_handler_preserves_coordinates")


def test_combine_handler_basic():
    """Test combine_handler generates texture patterns."""
    processor = HorizontalTextureProcessor(4, 4)
    # Set up test data
    cells = [GridCell(i % 4, i // 4, float(i), "empty") for i in range(16)]
    processor.ipo.input_data = cells

    result = combine_handler(processor, {})

    assert len(result) == 16
    # Check that texture types are now combined patterns
    for cell in result:
        assert "-" in cell.texture_type, f"Expected combined texture, got {cell.texture_type}"
        assert cell.texture_type != "empty", "Texture should be combined, not 'empty'"

    print("PASS: test_combine_handler_basic")


def test_combine_handler_empty_input():
    """Test combine_handler with empty input."""
    processor = HorizontalTextureProcessor(4, 4)
    processor.ipo.input_data = []

    result = combine_handler(processor, {})

    assert result == [], "Should return empty list for empty input"

    print("PASS: test_combine_handler_empty_input")


def test_combine_handler_pattern_cycling():
    """Test combine_handler cycles through generated patterns."""
    processor = HorizontalTextureProcessor(4, 4)
    cells = [GridCell(i % 4, i // 4, float(i), "empty") for i in range(16)]
    processor.ipo.input_data = cells

    result = combine_handler(processor, {})

    # Generate should create 2-tuple combinations from 4 patterns
    # So we expect 4 choose 2 = 6 combinations
    # The handler should cycle through these
    patterns = [cell.texture_type for cell in result]
    assert len(set(patterns)) > 1, "Should have multiple different patterns"

    print("PASS: test_combine_handler_pattern_cycling")


def test_render_handler_basic():
    """Test render_handler calls SpatialRender."""
    processor = HorizontalTextureProcessor(4, 4)
    cells = [GridCell(i % 4, i // 4, float(i), "empty") for i in range(16)]
    processor.ipo.input_data = cells
    processor.ipo.processed_data = cells

    result = render_handler(processor, {})

    # Should return processed_data if available
    assert result == cells
    assert len(result) == 16

    print("PASS: test_render_handler_basic")


def test_render_handler_fallback_to_input():
    """Test render_handler falls back to input_data when processed_data is None."""
    processor = HorizontalTextureProcessor(4, 4)
    cells = [GridCell(i % 4, i // 4, float(i), "empty") for i in range(16)]
    processor.ipo.input_data = cells
    processor.ipo.processed_data = None

    result = render_handler(processor, {})

    # Should fall back to input_data
    assert result == cells
    assert len(result) == 16

    print("PASS: test_render_handler_fallback_to_input")


def test_complete_handler_basic():
    """Test complete_handler returns current input_data."""
    processor = HorizontalTextureProcessor(4, 4)
    cells = [GridCell(i % 4, i // 4, float(i), "empty") for i in range(16)]
    processor.ipo.input_data = cells

    result = complete_handler(processor, {})

    assert result == cells
    assert len(result) == 16

    print("PASS: test_complete_handler_basic")


def test_complete_handler_empty():
    """Test complete_handler with empty input."""
    processor = HorizontalTextureProcessor(4, 4)
    processor.ipo.input_data = []

    result = complete_handler(processor, {})

    assert result == []

    print("PASS: test_complete_handler_empty")


def test_compliance_baseline_handler_with_temp_dir():
    """Test compliance_baseline_handler generates artifacts in temp directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        processor = HorizontalTextureProcessor(4, 4)
        processor.ipo.compliance_root = temp_dir
        processor.ipo.input_data = []

        compliance_baseline_handler(processor, {})

        # Check that files were created
        license_path = Path(temp_dir) / "LICENSE"
        notice_path = Path(temp_dir) / "NOTICE"
        terms_path = Path(temp_dir) / "TERMS_OF_ENGAGEMENT.md"

        assert license_path.exists(), "LICENSE file should be created"
        assert notice_path.exists(), "NOTICE file should be created"
        assert terms_path.exists(), "TERMS_OF_ENGAGEMENT.md should be created"

        # Check file contents
        license_content = license_path.read_text(encoding="utf-8")
        assert "Apache License" in license_content
        assert "Irfan Kabir" in license_content

        notice_content = notice_path.read_text(encoding="utf-8")
        assert "Mangrove — Compliance Notice" in notice_content

        terms_content = terms_path.read_text(encoding="utf-8")
        assert "Terms of Engagement" in terms_content
        assert "Generated by Apparat phase" in terms_content

        # Check that artifacts were recorded
        assert processor.ipo.compliance_artifacts is not None
        assert len(processor.ipo.compliance_artifacts) == 3

        print("PASS: test_compliance_baseline_handler_with_temp_dir")


def test_compliance_baseline_handler_idempotency():
    """Test compliance_baseline_handler doesn't overwrite existing files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        processor = HorizontalTextureProcessor(4, 4)
        processor.ipo.compliance_root = temp_dir
        processor.ipo.input_data = []

        # First run
        compliance_baseline_handler(processor, {})
        license_path = Path(temp_dir) / "LICENSE"
        original_content = license_path.read_text(encoding="utf-8")

        # Second run
        compliance_baseline_handler(processor, {})
        new_content = license_path.read_text(encoding="utf-8")

        # Content should be identical (file not overwritten)
        assert original_content == new_content

        print("PASS: test_compliance_baseline_handler_idempotency")


def test_compliance_baseline_handler_default_root():
    """Test compliance_baseline_handler uses default root when none specified."""
    processor = HorizontalTextureProcessor(4, 4)
    processor.ipo.compliance_root = None
    processor.ipo.input_data = []

    # Should use the parent directory of the phase_handlers.py file
    # We'll just check it doesn't crash and returns the input data
    result = compliance_baseline_handler(processor, {})

    assert result == processor.ipo.input_data
    assert processor.ipo.compliance_artifacts is not None

    print("PASS: test_compliance_baseline_handler_default_root")


def test_handler_chaining():
    """Test that handlers can be chained together."""
    processor = HorizontalTextureProcessor(4, 4)

    # Initiate
    initiate_handler(processor, {})
    assert len(processor.ipo.input_data) == 16

    # Set some values
    for i, cell in enumerate(processor.ipo.input_data):
        processor.ipo.input_data[i] = GridCell(cell.x, cell.y, float(i) / 10.0, cell.texture_type)

    # Quantize
    quantize_handler(processor, {})
    assert all(cell.value == round(cell.value * 10) / 10 for cell in processor.ipo.input_data)

    # Complete
    result = complete_handler(processor, {})
    assert len(result) == 16

    print("PASS: test_handler_chaining")


if __name__ == "__main__":
    test_initiate_handler_basic()
    test_initiate_handler_different_resolutions()
    test_quantize_handler_basic()
    test_quantize_handler_empty_input()
    test_quantize_handler_preserves_coordinates()
    test_combine_handler_basic()
    test_combine_handler_empty_input()
    test_combine_handler_pattern_cycling()
    test_render_handler_basic()
    test_render_handler_fallback_to_input()
    test_complete_handler_basic()
    test_complete_handler_empty()
    test_compliance_baseline_handler_with_temp_dir()
    test_compliance_baseline_handler_idempotency()
    test_compliance_baseline_handler_default_root()
    test_handler_chaining()
    print("\n✨ All phase handler tests passed!")
