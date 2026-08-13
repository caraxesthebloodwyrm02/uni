"""Regression guard: SpatialRender must be defined exactly once.

Background: at one point, ``class SpatialRender`` was defined in both
``api.py`` and ``horizontal_texture_processor.py`` with identical bodies.
The two class objects were distinct, so identity checks and
``isinstance`` calls behaved inconsistently depending on which module
an importer reached for. The duplicate was removed; this test prevents
it from coming back.

If a future test legitimately needs a second ``SpatialRender``, the
correct move is to parameterize the existing one (e.g. via constructor
flags), not to redefine it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

APPARAT_DIR = Path("mangrove_platform/apparat")
CLASS_RE = re.compile(r"^class\s+(\w+)\s*[:(]", re.MULTILINE)


def _class_definitions() -> dict[str, list[str]]:
    """Return ``{ClassName: [relative_path, ...]}`` for every class
    defined at module top level in ``mangrove_platform/apparat/*.py``.

    Skips the ``src/golding/`` accelerator (third-party) and any
    subpackage that lives under a non-apparat namespace.
    """
    seen: dict[str, list[str]] = {}
    if not APPARAT_DIR.is_dir():
        # Run from any cwd; pytest's testpaths config sets rootdir but
        # not the working directory. Resolve relative to this file's
        # parents as a fallback so the test is location-stable.
        candidates = [
            Path(__file__).resolve().parent.parent.parent / "mangrove_platform" / "apparat",
        ]
        apparat_root = next((p for p in candidates if p.is_dir()), None)
        if apparat_root is None:
            pytest.skip(reason=f"Could not locate apparat directory from {Path(__file__)}")
    else:
        apparat_root = APPARAT_DIR

    for py in sorted(apparat_root.glob("*.py")):
        if py.name == "__init__.py":
            continue
        text = py.read_text(encoding="utf-8")
        for match in CLASS_RE.finditer(text):
            seen.setdefault(match.group(1), []).append(py.name)
    return seen


def test_spatial_render_defined_exactly_once() -> None:
    """``SpatialRender`` must live in exactly one module under apparat/."""
    seen = _class_definitions()
    locations = seen.get("SpatialRender", [])
    assert len(locations) == 1, (
        f"SpatialRender is defined in {len(locations)} modules: {locations}. "
        "The canonical definition lives in mangrove_platform/apparat/api.py; "
        "downstream modules must import from there."
    )
    assert locations[0] == "api.py", (
        f"SpatialRender must live in api.py (got {locations[0]}). "
        "The api module is the foundation; redefinitions shadow it."
    )


def test_no_apparat_class_redefined_across_modules() -> None:
    """No top-level class in apparat/ may appear in more than one file.

    This is the broader invariant. It will flag any future duplicate
    class, not just ``SpatialRender``. Acceptable exceptions (e.g.
    re-exports in ``__init__.py``) are excluded by the regex only
    matching ``*.py`` files that are not ``__init__.py``.
    """
    seen = _class_definitions()
    duplicates = {name: files for name, files in seen.items() if len(files) > 1}
    assert not duplicates, (
        f"Duplicate class definitions found in apparat/: {duplicates}. "
        "Each class must be defined in exactly one module."
    )
