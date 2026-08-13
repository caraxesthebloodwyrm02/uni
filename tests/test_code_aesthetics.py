"""Tests for cosmetic consistency, code hygiene, and diagnostic validation."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_no_trailing_whitespace_or_missing_newlines():
    """Ensure all tracked Python source files end with a newline and have no trailing whitespace."""
    python_files = list((REPO_ROOT / "mangrove_platform").rglob("*.py")) + list(
        (REPO_ROOT / "scripts").rglob("*.py")
    )
    assert len(python_files) > 0

    for filepath in python_files:
        content = filepath.read_text(encoding="utf-8")
        if not content:
            continue

        # Must end with a single newline
        assert content.endswith("\n"), f"File {filepath.name} does not end with a newline"
        assert not content.endswith("\n\n"), f"File {filepath.name} ends with multiple blank lines"

        # Check trailing whitespace line by line
        for idx, line in enumerate(content.splitlines(), start=1):
            assert line == line.rstrip(), f"Trailing whitespace found in {filepath.name}:{idx}"


def test_apparat_init_all_export_consistency():
    """Verify that apparat package __all__ exports accurately reference valid module attributes."""
    import mangrove_platform.apparat as apparat

    assert hasattr(apparat, "__all__")
    for symbol in apparat.__all__:
        assert hasattr(apparat, symbol), (
            f"Symbol {symbol!r} listed in __all__ but not exported by apparat"
        )


def test_no_raw_print_statements_in_platform_code():
    """Verify no accidental print(...) statements exist in production core platform logic."""
    platform_dir = REPO_ROOT / "mangrove_platform"

    for py_file in platform_dir.rglob("*.py"):
        # Exclude CLI tool scripts and test runner helpers that explicitly output formatting/JSON to stdout
        if py_file.name in ("review_pack.py", "sisa.py", "test_server.py", "validate.py"):
            continue

        content = py_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Ignore comments or docstrings
            if stripped.startswith("#"):
                continue
            if "print(" in line:
                raise AssertionError(
                    f"Potential raw print statement in production code: {py_file.name}:{idx}"
                )


def test_logger_namespace_prefix_consistency():
    """Verify all logging.getLogger(...) calls use the canonical 'mangrove.' namespace prefix."""
    platform_dir = REPO_ROOT / "mangrove_platform"

    for py_file in platform_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for idx, line in enumerate(content.splitlines(), start=1):
            if "getLogger(" in line and not line.strip().startswith("#"):
                assert 'getLogger("mangrove.' in line or "getLogger('mangrove." in line, (
                    f"Non-canonical logger namespace in {py_file.name}:{idx}: {line.strip()}"
                )


def test_phase_enum_and_validation_consistency():
    """Verify all Phase enum values are valid phase names in ALLOWED_PHASES."""
    from mangrove_platform.apparat.api import Phase
    from mangrove_platform.apparat.phase_validation import (
        ALLOWED_PHASES,
        validate_phase_name,
    )

    for phase in Phase:
        assert phase.value in ALLOWED_PHASES
        assert validate_phase_name(phase.value) == phase.value


def test_mcp_pydantic_models_json_schema_validity():
    """Verify all MCP Pydantic request models produce valid JSON schemas."""
    from pydantic import BaseModel

    import mangrove_platform.mcp.security as mcp_sec

    for name in dir(mcp_sec):
        obj = getattr(mcp_sec, name)
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel:
            schema = obj.model_json_schema()
            assert "title" in schema
            assert "type" in schema or "properties" in schema


def test_pipeline_validation_edge_cases():
    """Verify validate_pipeline handles malformed input strings gracefully without crashing."""
    import pytest

    from mangrove_platform.apparat.phase_validation import validate_pipeline

    with pytest.raises(ValueError, match="Pipeline cannot be empty"):
        validate_pipeline("")

    with pytest.raises(ValueError, match="Invalid pipeline syntax"):
        validate_pipeline("initiate//complete")

    with pytest.raises(ValueError, match="Invalid pipeline syntax"):
        validate_pipeline("/initiate")
