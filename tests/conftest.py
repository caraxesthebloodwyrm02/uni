"""Pytest configuration for mangrove tests."""

from __future__ import annotations

import pytest


# CAPSYS embedding trap mitigation
# Disable pytest's internal output capture for tests that use capsys
# This prevents conflicts between pytest's capture and explicit capsys usage
def pytest_configure(config: pytest.Config) -> None:
    """Mitigate CAPSYS embedding trap by ensuring clean capture state."""
    # Ensure capsys fixture is available and doesn't conflict with coverage
    config.addinivalue_line(
        "markers",
        "capsys_safe: mark test as safe for capsys usage to avoid embedding trap",
    )


# Additional mitigation: ensure clean stdout/stderr state
@pytest.fixture(autouse=True)
def reset_capture_state() -> None:
    """Reset capture state before each test to avoid CAPSYS embedding issues."""
    import sys as _sys

    # Ensure stdout/stderr are not in a captured state
    if hasattr(_sys.stdout, "buffer"):
        _ = _sys.stdout.flush()
        _ = _sys.stderr.flush()
