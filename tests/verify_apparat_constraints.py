import sys

from mangrove_platform.mcp import apparat_logic


def probe(label, phase, width=4, height=4):
    print(f"[PROBE] {label} -> {phase}")
    res = apparat_logic.run_apparat_phase(phase, width, height)
    print(
        f"   Result: {res['status']} | {'Error: ' + res['error'] if 'error' in res else 'Data len: ' + str(len(res.get('result', [])))}"
    )
    return res


def test_consistency_and_constraints():
    print("Verifying Apparat Consistency and Call Constraint Accuracy...")

    # --- 1. Consistency: State Persistence ---
    print("\n--- [Consistency: State Persistence] ---")
    # Establish a state
    probe("Init", "initiate")
    probe("Scale", "scale:2.0")
    # Check if it's still there by running a phase that doesn't change data but reads it
    # 'invert' just flips values, so it's a good test of state existence
    res = probe("State Check", "invert")
    assert res["status"] == "success" and len(res["result"]) > 0, (
        "State should persist across calls"
    )
    print("[OK] State persistence verified.")

    # --- 2. Consistency: Resolution Reset ---
    print("\n--- [Consistency: Resolution Reset] ---")
    probe("Init 4x4", "initiate", 4, 4)
    probe("Scale 4x4", "scale:2.0", 4, 4)
    # Change resolution - should trigger a new processor
    res = probe("New Res 8x8", "initiate", 8, 8)
    assert res["status"] == "success" and len(res["result"]) == 64, (
        "Processor should reset and create 8x8 grid"
    )
    print("[OK] Resolution reset verified.")

    # --- 3. Constraint Accuracy: Type Violations ---
    print("\n--- [Constraint Accuracy: Type Violations] ---")
    # scale expects float
    probe("Type Error (Scale)", "scale:not_a_float")
    # clamp expects two floats
    probe("Type Error (Clamp)", "clamp:0.1,not_a_float")

    # --- 4. Constraint Accuracy: Parameter Count ---
    print("\n--- [Constraint Accuracy: Param Counts] ---")
    # scale expects 1 param (factor)
    probe("Too many params (Scale)", "scale:2.0,3.0")
    # clamp expects 2 params (min, max)
    probe("Too few params (Clamp)", "clamp:0.1")

    # --- 5. Constraint Accuracy: Syntax and Existence ---
    print("\n--- [Constraint Accuracy: Syntax/Existence] ---")
    probe("Non-existent Phase", "ghost_phase:1.0")
    probe("Malformed Syntax", "scale::2.0")
    probe("Empty Phase", "")

    print("\nConstraint and Consistency Probes Complete")


if __name__ == "__main__":
    try:
        test_consistency_and_constraints()
    except Exception as e:
        print(f"\n[CRITICAL FAILURE] {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
