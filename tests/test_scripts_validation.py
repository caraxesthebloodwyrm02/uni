"""Tests for project scripts to ensure modularity, configuration, and robustness."""

import subprocess
import sys
from pathlib import Path

from scripts.config_loader import get_setting


def test_config_loader():
    """Verify that get_setting retrieves values and returns defaults correctly."""
    assert get_setting(["environment", "staleBranchAgeDays"], 90) == 90
    assert get_setting(["environment", "complianceDirectory"], ".compliance-hand-off") == ".compliance-hand-off"
    assert get_setting(["nonexistent", "key"], "default_value") == "default_value"


def test_script_imports():
    """Verify that scripts can be imported cleanly without executing main code (modularity check)."""
    import scripts.attribution_oscillator as attribution_oscillator
    import scripts.profile_apparat as profile_apparat
    import scripts.warmup_apparat as warmup_apparat

    assert hasattr(profile_apparat, "profile_pipeline")

    assert hasattr(attribution_oscillator, "sha256_file")
    assert hasattr(warmup_apparat, "warmup")


def test_python_script_execution():
    """Verify that running python scripts with --help exits cleanly with code 0."""
    repo_root = Path(__file__).resolve().parent.parent



    # Test attribution_oscillator.py --help
    res = subprocess.run(  # noqa: S603
        [sys.executable, str(repo_root / "scripts" / "attribution_oscillator.py"), "--help"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "Attribution Chain" in res.stdout


def test_shell_script_execution():
    """Verify that shell scripts run and fail-fast or handle errors correctly."""
    repo_root = Path(__file__).resolve().parent.parent

    # Run audit_workspace.sh with a non-existent path and expect error
    res = subprocess.run(  # noqa: S603, S607
        ["/bin/bash", str(repo_root / "scripts" / "audit_workspace.sh"), "/nonexistent/path/123"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 1
    assert "ERROR: root does not exist" in res.stderr
