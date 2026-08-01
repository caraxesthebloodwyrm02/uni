import sys
from pathlib import Path

# Ensure mangrove root is in sys.path
mangrove_dir = Path(__file__).resolve().parent.parent.parent
platform_dir = mangrove_dir / "mangrove_platform"
for d in (str(platform_dir), str(mangrove_dir)):
    if d not in sys.path:
        sys.path.insert(0, d)

from apparat.api import ApparatValidationError  # noqa: E402
from apparat.apparat import register_phase_handler  # noqa: E402
from apparat.horizontal_texture_processor import (  # noqa: E402
    HorizontalTextureProcessor,
)


def probe(processor, phase, expected_error=None):
    print(f"🔍 Probing {phase}...", end=" ")
    try:
        processor.process_phase(phase)
        if expected_error:
            print(f"❌ FAILED: Expected {expected_error} but got success")
            return False
        print("✅ SUCCESS")
        return True
    except ApparatValidationError as e:
        if expected_error and expected_error in str(e):
            print(f"✅ CAUGHT: {str(e)}")
            return True
        print(f"❌ UNEXPECTED ERROR: {str(e)}")
        return False
    except Exception as e:
        print(f"💥 CRASH: {type(e).__name__}: {e}")
        return False


def test_robustness():
    print("🚀 Starting Apparat Robustness Verification...")
    processor = HorizontalTextureProcessor(10, 10)
    passed = 0
    total = 0

    # 1. Invalid Syntax — the regex is [a-zA-Z0-9_]+, so anything with whitespace,
    # punctuation, or non-identifier chars is rejected by the dispatcher.
    # Note: 'phase:arg1 arg2' and '123:arg' pass the regex (valid identifier +
    # colon-prefixed args), but fail the registry lookup — they're tested below.
    cases = [
        ("!!!", "Invalid phase syntax"),
        ("phase name with spaces", "Invalid phase syntax"),
    ]
    for p, e in cases:
        total += 1
        if probe(processor, p, e):
            passed += 1

    # 1b. Valid syntax but registry miss — these match the regex but the name
    # isn't registered (or '123' has no handler).
    for p in ("phase:arg1 arg2", "123:arg"):
        total += 1
        if probe(processor, p, "not found in registry"):
            passed += 1

    # 2. Registry Misses
    total += 1
    if probe(processor, "non_existent_phase", "not found in registry"):
        passed += 1

    # 3. Parameter Count (Too Many)
    total += 1
    if probe(processor, "scale:1.0,2.0", "Unexpected parameters for phase 'scale'"):
        passed += 1

    # 4. Parameter Count (Too Few)
    total += 1
    if probe(processor, "clamp:0.1", "Missing required parameter 'max_val'"):
        passed += 1

    # 5. Type Mismatch
    total += 1
    if probe(processor, "scale:abc", "must be of type float"):
        passed += 1

    # 6. Chaos Handler
    print("\nSetting up Chaos Handler...")

    def chaos_handler(proc, params):
        ctype = params.get("type")
        if ctype == "runtime":
            raise RuntimeError("Chaos RuntimeError!")
        if ctype == "attribute":
            raise AttributeError("Chaos AttributeError!")
        if ctype == "zero":
            raise ZeroDivisionError("Chaos ZeroDivisionError!")
        return []

    register_phase_handler("chaos_handler", signature={"type": str}, param_map=["type"])(
        chaos_handler
    )

    chaos_cases = [
        (
            "chaos_handler:runtime",
            "Unexpected error executing phase chaos_handler: Chaos RuntimeError!",
        ),
        (
            "chaos_handler:attribute",
            "Unexpected error executing phase chaos_handler: Chaos AttributeError!",
        ),
        (
            "chaos_handler:zero",
            "Unexpected error executing phase chaos_handler: Chaos ZeroDivisionError!",
        ),
    ]
    for p, e in chaos_cases:
        total += 1
        if probe(processor, p, e):
            passed += 1

    print(f"\n✨ Robustness Results: {passed}/{total} passed.")
    return passed == total


if __name__ == "__main__":
    if not test_robustness():
        sys.exit(1)
