import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

class TestAutomationWiring:
    """Verifies that the CI pipeline, hooks, and AUX scripts are correctly wired."""

    def test_ci_workflow_invokes_validators(self):
        """Ensure ci.yml properly invokes the consolidated workspace validator."""
        ci_yml_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
        if not ci_yml_path.exists():
            pytest.skip("ci.yml not found")

        content = ci_yml_path.read_text(encoding="utf-8")
        assert "uv run python scripts/validate_workspace.py" in content, "CI does not invoke validate_workspace.py"
        assert "uv run ruff check --fix" in content, "CI does not run ruff check --fix in quality gate"

    def test_validate_workspace_has_allowlist(self):
        """Ensure validate_workspace.py uses an explicit allowlist, not a broad prefix skip."""
        validator_path = REPO_ROOT / "scripts" / "validate_workspace.py"
        assert validator_path.exists(), "validate_workspace.py missing"
        
        content = validator_path.read_text(encoding="utf-8")
        assert "PATTERN_CHECK_ALLOWLIST" in content, "Validator is missing PATTERN_CHECK_ALLOWLIST"
        assert "PATTERN_CHECK_SKIP_PREFIXES" not in content, "Validator is using too-broad PATTERN_CHECK_SKIP_PREFIXES"

    def test_aux_scripts_exist_and_executable(self):
        """Ensure critical AUX scripts exist and have execute permissions."""
        scripts_to_check = [
            "scripts/attribution_oscillator.py",
            "scripts/validate_workspace.py",
            "scripts/prune-stale-branches.sh"
        ]

        for script in scripts_to_check:
            script_path = REPO_ROOT / script
            assert script_path.exists(), f"Missing AUX script: {script}"
            # Windows might not report os.X_OK reliably, but on Linux this should pass.
            if os.name == "posix":
                assert os.access(script_path, os.X_OK), f"Script not executable: {script}"
