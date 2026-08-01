#!/usr/bin/env python3
"""Test the regex-driven dispatcher in horizontal_texture_processor.py."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../mangrove_platform"))

from apparat.api import GridCell  # type: ignore
from apparat.horizontal_texture_processor import HorizontalTextureProcessor  # type: ignore


def test_dispatcher_without_params():
    """Test dispatcher with phase name only (no parameters)."""
    processor = HorizontalTextureProcessor(4, 4)
    # Manually set up test data
    cells = []
    for i in range(16):
        cells.append(GridCell(i % 4, i // 4, i % 5, "empty"))
    processor.ipo.input_data = cells

    # Test invert without parameters (no signature requirements)
    result = processor.process_phase("invert")
    assert len(result) == len(processor.ipo.input_data)
    for i, cell in enumerate(result):
        expected = 1.0 - (i % 5)
        assert cell.value == expected, f"Expected {expected}, got {cell.value} at index {i}"
    print("PASS: test_dispatcher_without_params")


def test_dispatcher_with_params():
    """Test dispatcher with parameters (e.g., scale:3.0)."""
    processor = HorizontalTextureProcessor(4, 4)
    # Manually set up test data
    cells = []
    for i in range(16):
        cells.append(GridCell(i % 4, i // 4, i % 5, "empty"))
    processor.ipo.input_data = cells

    # Test scale with parameter 3.0
    result = processor.process_phase("scale:3.0")
    assert len(result) == len(processor.ipo.input_data)
    for i, cell in enumerate(result):
        expected = (i % 5) * 3.0
        assert cell.value == expected, f"Expected {expected}, got {cell.value} at index {i}"
    print("PASS: test_dispatcher_with_params")


def test_dispatcher_with_multiple_params():
    """Test dispatcher with multiple parameters (e.g., clamp:0.0,5.0)."""
    processor = HorizontalTextureProcessor(4, 4)
    # Manually set up test data
    cells = []
    for i in range(16):
        cells.append(GridCell(i % 4, i // 4, i % 5, "empty"))
    processor.ipo.input_data = cells

    # Test clamp with parameters 0.0 and 5.0 (should clamp to [0.0, 5.0])
    result = processor.process_phase("clamp:0.0,5.0")
    assert len(result) == len(processor.ipo.input_data)
    for i, cell in enumerate(result):
        val = i % 5
        expected = max(0.0, min(5.0, float(val)))
        assert cell.value == expected, f"Expected {expected}, got {cell.value} at index {i}"
    print("PASS: test_dispatcher_with_multiple_params")


def test_dispatcher_invalid_phase():
    """Test dispatcher with invalid phase name."""
    processor = HorizontalTextureProcessor(4, 4)
    try:
        processor.process_phase("invalid_phase")
        raise AssertionError("Expected ApparatValidationError for invalid phase")
    except Exception as e:
        # Expected to raise ApparatValidationError
        assert "not found in registry" in str(e)
    print("PASS: test_dispatcher_invalid_phase")


if __name__ == "__main__":
    test_dispatcher_without_params()
    test_dispatcher_with_params()
    test_dispatcher_with_multiple_params()
    test_dispatcher_invalid_phase()
    print("All tests passed!")
