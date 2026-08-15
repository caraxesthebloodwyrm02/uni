#!/usr/bin/env python3
"""Test the regex-driven dispatcher in horizontal_texture_processor.py."""

from mangrove_platform.apparat.api import ApparatValidationError, GridCell
from mangrove_platform.apparat.apparat import register_phase_handler
from mangrove_platform.apparat.horizontal_texture_processor import (
    HorizontalTextureProcessor,
)


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


def test_dispatcher_edge_cases():
    """Test dispatcher boundary and edge cases for error handling."""
    processor = HorizontalTextureProcessor(4, 4)

    # 1. Syntax format errors
    for phase in ("!!!", "phase name with spaces"):
        try:
            processor.process_phase(phase)
            raise AssertionError(f"Expected ValidationError for '{phase}'")
        except ApparatValidationError as e:
            assert "Invalid phase syntax" in str(e)

    # 2. Too many args
    try:
        processor.process_phase("scale:1.0,2.0")
        raise AssertionError("Expected ValidationError for extra parameter")
    except ApparatValidationError as e:
        assert "Unexpected parameters" in str(e)

    # 3. Missing required arg
    try:
        processor.process_phase("clamp:0.1")
        raise AssertionError("Expected ValidationError for missing parameter")
    except ApparatValidationError as e:
        assert "Missing required parameter" in str(e)

    # 4. Type mismatch
    try:
        processor.process_phase("scale:abc")
        raise AssertionError("Expected ValidationError for type mismatch")
    except ApparatValidationError as e:
        assert "must be of type float" in str(e)

    # 5. Chaos Handler logic exception
    def chaos_handler(processor, params):
        ctype = params.get("type")
        if ctype == "runtime":
            raise RuntimeError("Chaos!")
        return []

    register_phase_handler("chaos_handler", signature={"type": str}, param_map=["type"])(
        chaos_handler
    )
    try:
        processor.process_phase("chaos_handler:runtime")
        raise AssertionError("Expected ApparatValidationError wrapping RuntimeError")
    except ApparatValidationError as e:
        assert "Unexpected error executing phase chaos_handler: Chaos!" in str(e)
    print("PASS: test_dispatcher_edge_cases")


if __name__ == "__main__":
    test_dispatcher_without_params()
    test_dispatcher_with_params()
    test_dispatcher_with_multiple_params()
    test_dispatcher_invalid_phase()
    test_dispatcher_edge_cases()
    print("All tests passed!")
