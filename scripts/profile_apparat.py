#!/usr/bin/env python3
# ==============================================================================
# Script Name: profile_apparat.py
# Description: Profile Apparat processing pipeline across different grid sizes.
# Scope/Safety: Safe / Read-only
# Dependencies: Python 3.13+, mangrove_platform (Apparat components)
# ==============================================================================
import sys
import time

from scripts.config_loader import get_setting

try:
    from mangrove_platform.apparat.horizontal_texture_processor import HorizontalTextureProcessor
    from mangrove_platform.mcp.apparat_logic import initialize_apparat
except ImportError as e:
    print(f"CRITICAL: Failed to import Apparat components: {e}", file=sys.stderr)
    print(
        "Please run this script using 'uv run' to ensure all dependencies are available.",
        file=sys.stderr,
    )
    sys.exit(1)


def profile_pipeline(width, height):
    initialize_apparat()
    processor = HorizontalTextureProcessor(width, height)
    pipeline = ["initiate", "scale:1.5", "normalize", "highlight", "complete"]

    start_time = time.perf_counter()
    for phase in pipeline:
        processor.process_phase(phase)
    end_time = time.perf_counter()

    return (end_time - start_time) * 1000  # ms


def main():
    sizes = get_setting(["environment", "profilingGridSizes"], [4, 16, 32, 64])
    results = {}
    for s in sizes:
        t = profile_pipeline(s, s)
        results[s] = t

    print("Profiling Results (Grid Size x Grid Size -> Latency):")
    for s in sizes:
        print(f"{s}x{s}: {results[s]:.2f}ms")


if __name__ == "__main__":
    main()
