"""Smoke tests for the mangrove workspace structure.

These tests pin the contract that the workspace's CLAUDE.md contains
the canonical sections future agents will read first.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"


@pytest.fixture(scope="module")
def claude_md_text() -> str:
    """Load the canonical CLAUDE.md once per module."""
    return CLAUDE_MD.read_text(encoding="utf-8")


class TestRequiredSections:
    """The CLAUDE.md must contain all the sections the README claims are binding."""

    @pytest.mark.parametrize(
        "heading",
        [
            "## Read Order",
            "## Hard Baseline",
            "## Interaction Style",
            "## Shell & Git Discipline",
            "## Debugging",
            "## Mangrove Ecosystem Overview",
            "## Common Commands",
            "## Technical Architecture & Dependencies",
            "## Commit Conventions",
            "## Governance & Safety",
        ],
    )
    def test_section_present(self, claude_md_text: str, heading: str) -> None:
        assert heading in claude_md_text, f"missing required section: {heading!r}"


class TestHardBaseline:
    """The Hard Baseline rules must be enforced — no editing them out."""

    def test_uv_run_required(self, claude_md_text: str) -> None:
        assert re.search(r"`uv run` for all Python", claude_md_text), (
            "Hard Baseline must require `uv run` for Python execution"
        )

    def test_no_sudo(self, claude_md_text: str) -> None:
        assert "No `sudo`" in claude_md_text or "no `sudo`" in claude_md_text.lower()

    def test_no_git_config_user(self, claude_md_text: str) -> None:
        assert "Never set `user.name`/`user.email`" in claude_md_text or re.search(
            r"Never run `git config user", claude_md_text
        )


class TestCommitConventions:
    """Conventional commits with scope are required."""

    def test_conventional_commit_examples_present(self, claude_md_text: str) -> None:
        for prefix in ("feat(scope):", "fix(scope):", "chore(scope):", "docs(scope):"):
            assert prefix in claude_md_text, f"missing conventional-commit example: {prefix!r}"

    def test_no_git_add_dot(self, claude_md_text: str) -> None:
        assert "git add -A" in claude_md_text or "git add ." in claude_md_text


class TestGovernanceAndSafety:
    """The trust contract, port blocks, and DO-NOT references must be present."""

    def test_tuv_001_referenced(self, claude_md_text: str) -> None:
        assert "TUV-001" in claude_md_text

    def test_3paa_shadow_referenced(self, claude_md_text: str) -> None:
        assert "3PAA-SHADOW" in claude_md_text

    def test_port_8788_policy_present(self, claude_md_text: str) -> None:
        assert "8788" in claude_md_text

    def test_do_not_html_referenced(self, claude_md_text: str) -> None:
        assert "DO-NOT.html" in claude_md_text


class TestEcosystemMap:
    """The directory map should reference the canonical rooms."""

    @pytest.mark.parametrize(
        "room",
        [
            "`docs/`",
            "`finance/`",
            "`intelligence/`",
            "`platform/`",
            "`productivity/`",
            "`operations/`",
            "`lab/`",
            "`workspace/`",
        ],
    )
    def test_room_listed(self, claude_md_text: str, room: str) -> None:
        assert room in claude_md_text, f"missing ecosystem room: {room!r}"


class TestDocumentationCorruption:
    """Regression test: no broken u\nv or u\n+v patterns in documentation."""

    @pytest.mark.parametrize(
        "doc_path",
        [
            REPO_ROOT / "AGENTS.md",
            REPO_ROOT / "CLAUDE.md",
            REPO_ROOT / "docs" / "usage.md",
            REPO_ROOT / "docs" / "SECURITY.md",
            REPO_ROOT / "docs" / "SECURITY_GUIDE.md",
            REPO_ROOT / ".devin" / "README.md",
        ],
    )
    def test_no_broken_uv_lines(self, doc_path: Path) -> None:
        """Ensure uv run commands are not split across lines (e.g., u\nv run ...)."""
        if not doc_path.exists():
            pytest.skip(f"{doc_path} does not exist")

        text = doc_path.read_text(encoding="utf-8")

        broken_patterns = [
            (r"^u\nv run", "broken uv line (u\\nv run)"),
            (r"^u\s+\nv run", "broken uv line with spaces (u \\nv run)"),
            (r"\bu\n\+v run", "broken diff line (u\\n+v run)"),
        ]

        for pattern, desc in broken_patterns:
            assert not re.search(
                pattern, text, re.MULTILINE
            ), f"{doc_path.name}: Found {desc}"

    def test_validate_workspace_py_referenced(self) -> None:
        """Main validation script should be uv run python scripts/validate_workspace.py."""
        doc_files = [
            REPO_ROOT / "AGENTS.md",
            REPO_ROOT / "CLAUDE.md",
            REPO_ROOT / "docs" / "usage.md",
        ]

        for doc_path in doc_files:
            if doc_path.exists():
                text = doc_path.read_text(encoding="utf-8")
                assert (
                    "uv run python scripts/validate_workspace.py" in text
                ), f"{doc_path.name}: should reference uv run python scripts/validate_workspace.py"
