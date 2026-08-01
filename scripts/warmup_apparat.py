#!/usr/bin/env python3
"""
Apparat Runtime Warmup Script
Bootstraps the Apparat registry and executes a representative phase pipeline
to verify the health of the Apparat subsystem.
"""

import sys
from pathlib import Path

# Ensure we can import from the mangrove root
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent  # /home/cable/series/mangrove
sys.path.insert(0, str(root_dir.parent))  # Add /home/cable/series to path

try:
    from apparat.apparat import list_registered_phases
    from apparat.horizontal_texture_processor import HorizontalTextureProcessor
    from mcp.apparat_logic import initialize_apparat
except ImportError as e:
    print(f"CRITICAL: Failed to import Apparat components: {e}")
    sys.exit(1)


def warmup():
    print("🚀 Starting Apparat Runtime Warmup...")
    print("-" * 50)

    # 1. Initialization
    print("\n[1/4] Initializing Apparat Registry...")
    try:
        initialize_apparat()
        print("✓ Apparat initialized successfully")
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        sys.exit(1)

    # 2. Phase Registry Verification
    print("\n[2/4] Verifying Phase Registry...")
    phases = list_registered_phases()
    print(f"Registered phases: {len(phases)}")
    if len(phases) < 12:
        print(f"⚠️ Warning: Only {len(phases)}/12 phases registered.")
    else:
        print("✓ Registry fully populated")

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

        print("✓ Pipeline execution successful")
    except Exception as e:
        print(f"✗ Pipeline failed: {e}")
        sys.exit(1)

    # 4. Final State Inspection
    print("\n[4/4] Inspecting Final Grid Sample...")
    final_cells = processor.ipo.input_data
    if final_cells:
        sample = final_cells[0]
        print(f"  Sample Cell(0,0): Value={sample.value:.3f}, Type={sample.texture_type}")
        print("✓ Final state verified")
    else:
        print("✗ Error: Final grid is empty")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("🌟 Apparat Runtime Warmup COMPLETE")
    print("System is hot and ready for operation.")
    print("=" * 50)


if __name__ == "__main__":
    warmup()
