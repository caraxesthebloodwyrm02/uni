import sys
from pathlib import Path

# Ensure mangrove root is in sys.path
root = Path(__file__).resolve().parent.parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# Bootstrap registry: phase_handlers.py defines handlers (initiate, quantize,
# combine, render, complete) but does not register them at import time. Mirror
# what sisa._auto_register_handlers does — register them here explicitly.
from mangrove.platform.apparat import phase_handlers as _phase_handlers  # noqa: E401, E402
from mangrove.platform.apparat.apparat import register_phase_handler  # noqa: E402
from mangrove.platform.apparat.horizontal_texture_processor import (  # noqa: E402
    HorizontalTextureProcessor,
)

_register = register_phase_handler
_register("initiate", signature={})(_phase_handlers.initiate_handler)
_register("quantize", signature={})(_phase_handlers.quantize_handler)
_register("combine", signature={})(_phase_handlers.combine_handler)
_register("render", signature={})(_phase_handlers.render_handler)
_register("complete", signature={})(_phase_handlers.complete_handler)
_register("compliance_baseline", signature={})(_phase_handlers.compliance_baseline_handler)


def test_diagnostics():
    print("🚀 Starting Apparat Diagnostic Verification...")

    # Test 1: Length Invariance
    print("\nTesting Length Invariance...")
    res_4x4 = 4 * 4
    res_8x8 = 8 * 8

    phases_to_test = ["initiate", "scale:2.0", "normalize", "invert", "highlight", "complete"]

    for res in [res_4x4, res_8x8]:
        w = 4 if res == res_4x4 else 8
        h = 4 if res == res_4x4 else 8
        processor = HorizontalTextureProcessor(w, h)

        # Need to initiate first to fill the grid
        processor.process_phase("initiate")

        for phase in phases_to_test:
            result = processor.process_phase(phase)
            if len(result) != res:
                print(f"❌ FAILED: Phase {phase} returned {len(result)} cells instead of {res}")
                return False
        print(f"✅ {w}x{h} grid length invariance passed.")

    # Test 2: Coordinate Integrity
    print("\nTesting Coordinate Integrity...")
    processor = HorizontalTextureProcessor(2, 2)
    processor.process_phase("initiate")
    input_coords = [(c.x, c.y) for c in processor.ipo.input_data]

    # Run a pipeline
    processor.process_phase("scale:2.0")
    processor.process_phase("invert")

    output_coords = [(c.x, c.y) for c in processor.ipo.input_data]
    if input_coords != output_coords:
        print("❌ FAILED: Coordinates were mutated during processing")
        return False
    print("✅ Coordinate integrity verified.")

    # Test 3: Empty State Stability
    print("\nTesting Empty State Stability...")
    processor = HorizontalTextureProcessor(4, 4)
    processor.ipo.input_data = []

    try:
        # Some phases like 'normalize' or 'scale' should return [] if input is empty
        # according to their current implementation.
        res = processor.process_phase("scale:2.0")
        if res != []:
            print("❌ FAILED: scale should return [] for empty input")
            return False

        res = processor.process_phase("normalize")
        if res != []:
            print("❌ FAILED: normalize should return [] for empty input")
            return False

        print("✅ Empty state stability verified.")
    except Exception as e:
        print(f"❌ CRASHED on empty state: {e}")
        return False

    print("\n✨ All Diagnostics Passed ✨")
    return True


if __name__ == "__main__":
    if not test_diagnostics():
        sys.exit(1)
