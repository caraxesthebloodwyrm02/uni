import sys

try:
    from mangrove_platform.mcp import apparat_logic

    print("[OK] Imported apparat_logic")
except ImportError as e:
    print(f"[FAIL] Failed to import apparat_logic: {e}")
    sys.exit(1)


def test_surface():
    print("\n--- Driving Apparat Surface ---")

    # 1. State Persistence & Happy Path
    print("\n[1] Testing State Persistence & Happy Path...")
    # Initial grid 4x4
    res1 = apparat_logic.run_apparat_phase("initiate", 4, 4)
    if res1["status"] == "success":
        print(f"  [OK] Initiate: {len(res1['result'])} cells created")
    else:
        print(f"  [FAIL] Initiate failed: {res1['error']}")
        return

    # Scale by 2.0 (Positional arg)
    res2 = apparat_logic.run_apparat_phase("scale:2.0")
    if res2["status"] == "success":
        print("  [OK] Scale 2.0: Success")
        # Check if value increased (assuming 0.0 init, but scale 2.0 on 0.0 is 0.0)
        # Let's check a handler that actually changes values
    else:
        print(f"  [FAIL] Scale failed: {res2['error']}")

    # 2. High-Accuracy I/O (Parameter Validation)
    print("\n[2] Testing High-Accuracy I/O (Type Validation)...")

    # Scale expects a float. Pass a string that can't be cast.
    res3 = apparat_logic.run_apparat_phase("scale:not_a_float")
    if res3["status"] == "error":
        print(f"  [OK] Validation caught bad type: {res3['error']}")
    else:
        print(f"  [FAIL] Validation failed to catch bad type! Result: {res3['status']}")

    # Clamp expects two floats. Pass only one.
    res4 = apparat_logic.run_apparat_phase("clamp:0.1")
    if res4["status"] == "error":
        print(f"  [OK] Validation caught missing parameter: {res4['error']}")
    else:
        print(f"  [FAIL] Validation failed to catch missing parameter! Result: {res4['status']}")

    # 3. Registry Health
    print("\n[3] Testing Registry Surface...")
    phases = apparat_logic.list_apparat_phases()
    print(f"  Found {len(phases)} registered phases.")
    if "initiate" in phases and "highlight" in phases:
        print("  [OK] Basic phases present")
    else:
        print("  [FAIL] Critical phases missing")


if __name__ == "__main__":
    test_surface()
