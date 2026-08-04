import pytest

from mangrove_platform.apparat.api import GridCell
from mangrove_platform.apparat.apparat import PHASE_REGISTRY
from mangrove_platform.apparat.horizontal_texture_processor import HorizontalTextureProcessor

# Only test handlers registered by apparat.py at import time that are pure
# grid-cell transformations.  This isolates diagnostics from:
#   - validate_acceleration (external golding dependency)
#   - filter (changes output length — tested separately)
#   - any test-only handlers leaked into PHASE_REGISTRY by other test modules
_BUILTIN_HANDLERS = {"normalize", "scale", "clamp", "invert", "highlight"}
_BUILTIN_WITH_FILTER = _BUILTIN_HANDLERS | {"filter"}


@pytest.fixture
def processor_4x4():
    return HorizontalTextureProcessor(width=4, height=4)


@pytest.fixture
def processor_8x8():
    return HorizontalTextureProcessor(width=8, height=8)


def test_length_invariance(processor_4x4):
    """
    For every handler except 'filter', assert that result length == width * height.
    """
    width, height = processor_4x4.resolution
    expected_len = width * height

    # Setup: Fill input_data with correct number of cells
    cells = [GridCell(x, y, 0.5, "test") for y in range(height) for x in range(width)]
    processor_4x4.ipo.input_data = cells

    for phase_name, (handler, _, _) in PHASE_REGISTRY.items():
        if phase_name not in _BUILTIN_HANDLERS:
            continue

        # Reset input data between handlers to avoid cumulative changes
        processor_4x4.ipo.input_data = list(cells)

        result = handler(processor_4x4, {})
        assert len(result) == expected_len, (
            f"Handler '{phase_name}' failed length invariance: expected {expected_len}, got {len(result)}"
        )


def test_coordinate_integrity(processor_4x4):
    """
    Assert that GridCell.x and GridCell.y in the output exactly match the input coordinates.
    """
    width, height = processor_4x4.resolution
    cells = [GridCell(x, y, 0.5, "test") for y in range(height) for x in range(width)]
    processor_4x4.ipo.input_data = cells

    for phase_name, (handler, _, _) in PHASE_REGISTRY.items():
        if phase_name not in _BUILTIN_WITH_FILTER:
            continue
        # 'filter' is allowed to change length, but coordinates of remaining cells must be preserved
        processor_4x4.ipo.input_data = list(cells)

        result = handler(processor_4x4, {})

        # We check that every cell in result was also in input with the same coordinates
        # Since result is usually a transformation of input, we check indices if length is preserved
        if phase_name != "filter":
            assert len(result) == len(cells)
            for i in range(len(result)):
                assert result[i].x == cells[i].x, (
                    f"Handler '{phase_name}' corrupted x-coordinate at index {i}"
                )
                assert result[i].y == cells[i].y, (
                    f"Handler '{phase_name}' corrupted y-coordinate at index {i}"
                )
        else:
            # For filter, we just ensure the remaining cells still have their original coords
            # (which is trivial since filter just slices the list)
            for cell in result:
                # find if this cell exists in the original set with same coords
                # (since we use the same objects or identical ones)
                exists = any(c.x == cell.x and c.y == cell.y for c in cells)
                assert exists, (
                    f"Handler 'filter' produced a cell with coordinates {cell.x}, {cell.y} not present in input"
                )


def test_empty_state_stability(processor_4x4):
    """
    Verify that calling handlers when ipo.input_data is empty returns [] and does not crash.
    """
    processor_4x4.ipo.input_data = []

    for phase_name, (handler, _, _) in PHASE_REGISTRY.items():
        if phase_name not in _BUILTIN_WITH_FILTER:
            continue
        try:
            result = handler(processor_4x4, {})
            assert result == [], (
                f"Handler '{phase_name}' should return empty list for empty input, got {result}"
            )
        except Exception as e:
            pytest.fail(reason=f"Handler '{phase_name}' crashed on empty input: {e}")


def test_resolution_transitions(processor_4x4, processor_8x8):
    """
    Verify that changing dimensions (e.g., 4x4 to 8x8) resets the internal state
    and produces the correct number of cells.
    """
    # Test 4x4
    from mangrove_platform.apparat.phase_handlers import initiate_handler

    res_4 = initiate_handler(processor_4x4, {})
    assert len(res_4) == 4 * 4

    # Test 8x8
    res_8 = initiate_handler(processor_8x8, {})
    assert len(res_8) == 8 * 8

    # Ensure the 4x4 processor didn't accidentally change
    assert processor_4x4.resolution == (4, 4)
    assert processor_8x8.resolution == (8, 8)
