#!/usr/bin/env python3
# ==============================================================================
# Script Name: warmup_apparat.py
# Description: Warm up Apparat subsystem by bootstrapping the registry and verifying phase executions
# Scope/Safety: Safe / Read-only smoke validation
# Dependencies: Python 3.13+, mangrove_platform (Apparat components)
# ==============================================================================
"""
Apparat Runtime Warmup Script
Bootstraps the Apparat registry and executes a representative phase pipeline
to verify the health of the Apparat subsystem.

The `mangrove` project is installed editable by `uv sync` (per pyproject.toml),
so absolute imports of `mangrove_platform.apparat.X` and `mangrove_platform.mcp.X`
resolve under `uv run` from any CWD. No sys.path manipulation needed.
"""

import sys

try:
    from mangrove_platform.apparat.apparat import list_registered_phases
    from mangrove_platform.apparat.horizontal_texture_processor import (
        HorizontalTextureProcessor,
    )
    from mangrove_platform.mcp.apparat_logic import initialize_apparat
except ImportError as e:
    print(f"CRITICAL: Failed to import Apparat components: {e}")
    sys.exit(1)


def warmup():
    print("Starting Apparat Runtime Warmup...")
    print("-" * 50)

    # 1. Initialization
    print("\n[1/4] Initializing Apparat Registry...")
    try:
        initialize_apparat()
        print("[OK] Apparat initialized successfully")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        sys.exit(1)

    # 2. Phase Registry Verification
    print("\n[2/4] Checking Phase Registry...")
    phases = list_registered_phases()
    print(f"Registered phases: {len(phases)}")
    if not phases:
        print("[WARN] No phases registered.")
    else:
        print(f"[OK] Registry populated ({len(phases)} phases)")

    # 3. Execution Pipeline Smoke Test
    print(
        "\n[3/4] Running Sample Pipeline (initiate -> scale -> normalize -> highlight -> complete)..."
    )
    try:
        # 4x4 grid for a quick warmup
        processor = HorizontalTextureProcessor(4, 4)

        pipeline = ["initiate", "scale:1.5", "normalize", "highlight", "complete"]

        for phase in pipeline:
            result = processor.process_phase(phase)
            print(f"  Executing {phase: <15} ... OK (cells: {len(result)})")

        print("[OK] Pipeline execution successful")
    except Exception as e:
        print(f"[FAIL] Pipeline failed: {e}")
        sys.exit(1)

    # 4. Final State Inspection
    print("\n[4/4] Inspecting Final Grid Sample...")
    final_cells = processor.ipo.input_data
    if final_cells:
        sample = final_cells[0]
        print(f"  Sample Cell(0,0): Value={sample.value:.3f}, Type={sample.texture_type}")
        print("[OK] Final state inspected")
    else:
        print("[FAIL] Error: Final grid is empty")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("Apparat Runtime Warmup complete.")
    print("=" * 50)


if __name__ == "__main__":
    warmup()
