import sys
from pathlib import Path

# Ensure mangrove root is in sys.path
root = Path(__file__).resolve().parent.parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from mcp import apparat_logic  # noqa: E402


def test_pipeline_success():
    print("Testing Pipeline Success Path...")
    pipeline = "initiate/scale:2.0/normalize/complete"
    res = apparat_logic.run_apparat_pipeline(pipeline, 4, 4)

    assert res["status"] == "success", f"Pipeline failed: {res.get('error')}"
    assert len(res["executed_phases"]) == 4, "Should have executed 4 phases"
    assert res["executed_phases"] == ["initiate", "scale:2.0", "normalize", "complete"]
    assert len(res["result"]) == 16, "Should have 16 cells for 4x4"
    print("✅ Pipeline success verified.")


def test_pipeline_failure():
    print("\nTesting Pipeline Failure Path...")
    # Mid-pipeline failure: scale:invalid
    pipeline = "initiate/scale:invalid/complete"
    res = apparat_logic.run_apparat_pipeline(pipeline, 4, 4)

    assert res["status"] == "error", "Pipeline should have failed"
    assert res["failed_phase"] == "scale:invalid", "Should fail at scale phase"
    assert "executed_phases" in res and res["executed_phases"] == ["initiate"], (
        "Only initiate should have completed"
    )
    print("✅ Pipeline mid-failure verified.")


def test_state_transparency():
    print("\nTesting State Transparency...")
    # Initial state
    state = apparat_logic.get_apparat_state(4, 4)
    print(f"Initial state: {state['current_phase']}")

    # Run a phase
    apparat_logic.run_apparat_phase("initiate", 4, 4)
    state = apparat_logic.get_apparat_state(4, 4)
    assert state["current_phase"] == "initiate" or state["current_phase"] == "INITIATE", (
        "Phase should be update to initiate"
    )
    print("✅ State tracking verified.")


def test_resolution_reset_in_pipeline():
    print("\nTesting Resolution Reset in Pipeline...")
    # 4x4 pipeline
    apparat_logic.run_apparat_pipeline("initiate", 4, 4)
    state_4x4 = apparat_logic.get_apparat_state(4, 4)
    assert state_4x4["cell_count"] == 16

    # Change to 8x8 pipeline
    apparat_logic.run_apparat_pipeline("initiate", 8, 8)
    state_8x8 = apparat_logic.get_apparat_state(8, 8)
    assert state_8x8["cell_count"] == 64, "Processor should have reset to 8x8"
    print("✅ Resolution reset verified.")


if __name__ == "__main__":
    try:
        test_pipeline_success()
        test_pipeline_failure()
        test_state_transparency()
        test_resolution_reset_in_pipeline()
        print("\n✨ ALL PIPELINE TESTS PASSED ✨")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
