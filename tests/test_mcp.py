import sys

from mangrove_platform.mcp import apparat_logic


def test_mcp_api():
    print("Starting Apparat MCP API Test Suite...")

    # 1. Health Check
    print("\nTesting check_apparat_health()...")
    health = apparat_logic.check_apparat_health()
    print(f"Ready: {health.get('ready')}")
    assert health.get("ready") is True, "Subsystem should be ready"
    assert len(health.get("phases_resolved", [])) > 0, "Phases should be resolved"
    print("[OK] Health check passed.")

    # 2. List Phases
    print("\nTesting list_apparat_phases()...")
    phases = apparat_logic.list_apparat_phases()
    print(f"Found {len(phases)} phases: {phases}")
    assert isinstance(phases, list), "Should return a list"
    assert "initiate" in phases, "Initiate phase must be registered"
    print("[OK] Phase listing passed.")

    # 3. Run Phase: Success Path (Initiate -> Scale)
    print("\nTesting run_apparat_phase (Success Path)...")

    # Step A: Initiate
    init_res = apparat_logic.run_apparat_phase("initiate")
    print(f"Initiate: {init_res['status']}")
    assert init_res["status"] == "success", f"Initiate failed: {init_res.get('error')}"

    # Step B: Scale with valid params
    scale_res = apparat_logic.run_apparat_phase("scale:2.0")
    print(f"Scale (2.0): {scale_res['status']}")
    assert scale_res["status"] == "success", f"Scale failed: {scale_res.get('error')}"

    # Step C: Validate Acceleration
    val_res = apparat_logic.run_apparat_phase("validate_acceleration")
    print(f"Validate Acceleration: {val_res['status']}")
    assert val_res["status"] == "success", f"Validation failed: {val_res.get('error')}"
    print("[OK] Success path passed.")

    # 4. Run Phase: Error Path (Malformed Input)
    print("\nTesting run_apparat_phase (Error Path)...")
    # Passing a non-float to scale
    err_res = apparat_logic.run_apparat_phase("scale:not_a_number")
    print(f"Scale (not_a_number): {err_res['status']}")
    assert err_res["status"] == "error", "Malformed input should return error status"
    assert "error" in err_res, "Response must contain error message"
    print("[OK] Error handling passed.")

    # 5. Constraint Search
    print("\nTesting search_constraints()...")
    constraints = apparat_logic.search_constraints("regex")
    print(f"Found {len(constraints)} constraints.")
    assert isinstance(constraints, list), "Should return a list"
    print("[OK] Constraint search passed.")

    print("\nALL MCP API TESTS PASSED")


if __name__ == "__main__":
    try:
        test_mcp_api()
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
