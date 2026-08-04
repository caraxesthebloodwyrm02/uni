import sys

from mangrove_platform.mcp.apparat_logic import (
    list_apparat_phases,
    run_apparat_phase,
    search_constraints,
)


def test_list_phases():
    print("Testing list_apparat_phases...")
    phases = list_apparat_phases()
    print(f"Found {len(phases)} phases: {phases}")
    assert len(phases) >= 13
    print("[OK] Success\n")


def test_run_phase():
    print("Testing run_apparat_phase sequence...")
    # First, run initiate to populate the grid
    init_result = run_apparat_phase("initiate", width=2, height=2)
    print(f"Initiate status: {init_result['status']}, cells: {len(init_result.get('result', []))}")
    if init_result["status"] != "success" or len(init_result.get("result", [])) == 0:
        print(f"[FAIL] Initiate failed: {init_result.get('error', 'No cells returned')}")
        sys.exit(1)

    # Now run scale:2.0
    scale_result = run_apparat_phase("scale:2.0", width=2, height=2)
    print(f"Scale status: {scale_result['status']}, cells: {len(scale_result.get('result', []))}")
    if scale_result["status"] == "success" and len(scale_result.get("result", [])) == 4:
        print("[OK] Success\n")
    else:
        print(f"[FAIL] Scale failed: {scale_result.get('error', 'Unexpected cell count')}")
        sys.exit(1)


def test_search_constraints():
    print("Testing search_constraints...")
    results = search_constraints()
    print(f"Found {len(results)} constraints.")
    found_dispatcher = any("horizontal_texture_processor.py" in r["file"] for r in results)
    if found_dispatcher:
        print("[OK] Found dispatcher regex\n")
    else:
        print("[FAIL] Did not find dispatcher regex\n")


if __name__ == "__main__":
    try:
        test_list_phases()
        test_run_phase()
        test_search_constraints()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed with exception: {e}")
        sys.exit(1)
