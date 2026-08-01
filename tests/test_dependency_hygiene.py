"""Dependency hygiene tracking telemetry - Phase 1 baseline monitoring."""

import datetime
import json
import subprocess
import sys
from pathlib import Path


def test_dependency_tracking():
    """Track dependency-related metrics for baseline monitoring."""
    print("=== Dependency Hygiene Tracking ===")
    print(f"Timestamp: {datetime.datetime.now().isoformat()}")

    metrics = {
        "timestamp": datetime.datetime.now().isoformat(),
        "phase": "1-monitoring",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }

    # Try to get dependency count using uv
    try:
        result = subprocess.run(
            ["uv", "pip", "list"], capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        dep_lines = [line for line in result.stdout.split("\n") if line.strip()]
        metrics["dependency_count"] = len(dep_lines)
        metrics["uv_available"] = True
        print(f"Dependencies found: {len(dep_lines)}")
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        metrics["dependency_count"] = 0
        metrics["uv_available"] = False
        metrics["uv_error"] = str(e)
        print(f"uv not available: {e}")

    # Check for lockfile
    lockfile_path = Path(__file__).parent.parent / "uv.lock"
    if lockfile_path.exists():
        metrics["has_lockfile"] = True
        lockfile_size = lockfile_path.stat().st_size
        metrics["lockfile_size_bytes"] = lockfile_size
        print(f"Lockfile size: {lockfile_size} bytes")
    else:
        metrics["has_lockfile"] = False
        print("No lockfile found")

    # Check for pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        metrics["has_pyproject"] = True
        print("pyproject.toml found")
    else:
        metrics["has_pyproject"] = False
        print("No pyproject.toml found")

    # Save metrics
    metrics_file = Path(__file__).parent.parent / ".dependency-metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nMetrics saved to: {metrics_file}")
    print("\n=== Phase 1 Monitoring Complete ===")
    print("Next steps:")
    print("1. Run this test monthly after Dependabot updates")
    print("2. Compare metrics across cycles to identify patterns")
    print("3. Adjust Dependabot config based on data collected")

    # Always pass - this is for monitoring, not strict testing
    assert True
