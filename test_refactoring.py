#!/usr/bin/env python3
# ruff: noqa: S101
# ==============================================================================
# Script Name: test_refactoring.py
# Description: Test script to verify the HorizontalTextureProcessor and MCP refactoring changes
# Scope/Safety: Safe / Read-only verification
# Dependencies: Python 3.13+, Apparat/MCP components
# ==============================================================================
"""
Test script to verify the refactoring changes work correctly.
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_dispatch_phase():
    """Test that the _dispatch_phase method works correctly."""
    try:
        from mangrove_platform.apparat.api import GridCell
        from mangrove_platform.apparat.horizontal_texture_processor import (
            HorizontalTextureProcessor,
        )

        print("✓ Successfully imported HorizontalTextureProcessor")

        # Test each method
        processor = HorizontalTextureProcessor(4, 4)

        # Test _initiate
        result = processor._initiate()
        assert len(result) == 16, f"Expected 16 cells, got {len(result)}"
        assert all(cell.value == 0.0 for cell in result), "All cells should have value 0.0"
        print("✓ _initiate() works correctly")

        # Test _quantize
        processor.ipo.input_data = [
            GridCell(0, 0, 0.123456, "empty"),
            GridCell(1, 0, 1.6789, "empty"),
        ]
        result = processor._quantize()
        assert len(result) == 2, f"Expected 2 cells, got {len(result)}"
        assert result[0].value == 0.1, f"Expected 0.1, got {result[0].value}"
        assert result[1].value == 1.7, f"Expected 1.7, got {result[1].value}"
        print("✓ _quantize() works correctly")

        # Test _combine
        processor.ipo.input_data = [GridCell(i % 4, i // 4, float(i), "empty") for i in range(16)]
        result = processor._combine()
        assert len(result) == 16, f"Expected 16 cells, got {len(result)}"
        # Check that texture types are combined patterns
        for cell in result:
            assert "-" in cell.texture_type, f"Expected combined texture, got {cell.texture_type}"
        print("✓ _combine() works correctly")

        # Test _render
        processor.ipo.input_data = [GridCell(i % 4, i // 4, float(i), "empty") for i in range(16)]
        processor.ipo.processed_data = processor.ipo.input_data
        result = processor._render()
        assert result == processor.ipo.processed_data, "_render should return processed_data"
        print("✓ _render() works correctly")

        # Test _complete
        processor.ipo.input_data = [GridCell(i % 4, i // 4, float(i), "empty") for i in range(16)]
        result = processor._complete()
        assert result == processor.ipo.input_data, "_complete should return input_data"
        print("✓ _complete() works correctly")

        print("\n🎉 All dispatch phase tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error in dispatch phase test: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_error_discriminant():
    """Test that the isinstance discriminant works correctly."""
    try:
        from mangrove_platform.mcp.security import _ErrorResult, _ValidationFailedResult

        print("✓ Successfully imported error result classes")

        # Test that _ValidationFailedResult is an instance of _ErrorResult
        validation_error = _ValidationFailedResult(error="Test validation error")
        assert isinstance(validation_error, _ErrorResult), (
            "_ValidationFailedResult should be instance of _ErrorResult"
        )
        print("✓ isinstance(_ValidationFailedResult, _ErrorResult) works correctly")

        # Test that _ErrorResult is an instance of _ErrorResult
        error_result = _ErrorResult(error="Test error")
        assert isinstance(error_result, _ErrorResult), (
            "_ErrorResult should be instance of _ErrorResult"
        )
        print("✓ isinstance(_ErrorResult, _ErrorResult) works correctly")

        print("\n🎉 All error discriminant tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error in error discriminant test: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing refactoring changes...\n")

    success1 = test_dispatch_phase()
    print()
    success2 = test_error_discriminant()

    if success1 and success2:
        print("\n✅ All tests passed! Refactoring is successful.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
