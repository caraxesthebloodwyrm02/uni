import pytest

from mangrove_platform.apparat.api import ApparatValidationError, GridCell
from mangrove_platform.apparat.horizontal_texture_processor import HorizontalTextureProcessor


def test_recursion_safeguard_prevents_infinite_loop():
    """
    Test that the _processing_depth recursion safeguard successfully stops
    a malicious or misconfigured hook from causing infinite recursion via process_phase.
    """
    processor = HorizontalTextureProcessor(4, 4)

    # A malicious hook that calls process_phase again
    def recursive_hook(proc, name, data):
        return proc.process_phase("quantize")

    processor.register_hook("pre", "quantize", recursive_hook)

    # Register the 'quantize' phase handler
    from mangrove_platform.apparat.apparat import register_phase_handler
    from mangrove_platform.apparat.phase_handlers import quantize_handler

    register_phase_handler("quantize", signature={})(quantize_handler)

    # Set some initial data
    processor.ipo.input_data = [GridCell(0, 0, 0.1, "empty")]

    # Calling it should raise an ApparatValidationError rather than RecursionError
    with pytest.raises(ApparatValidationError) as exc_info:
        processor.process_phase("quantize")

    assert "Maximum processing depth exceeded" in str(exc_info.value)


if __name__ == "__main__":
    test_recursion_safeguard_prevents_infinite_loop()
    print("PASS: test_recursion_safeguard_prevents_infinite_loop")
