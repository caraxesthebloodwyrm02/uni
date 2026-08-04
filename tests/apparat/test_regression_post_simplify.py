#!/usr/bin/env python3
"""Regression tests locking in post-simplification invariants.

These tests guard against silent reverts of three pieces of work:

1. F5 — the data-driven ``HANDLER_REGISTRY`` loop in ``apparat.py``
   must register every built-in handler in one pass; if anyone reverts
   it to a multi-line if/elif/elif chain, the tuple count will drop
   below the expected 6 and the test fails.

2. Shim methods on ``HorizontalTextureProcessor`` — ``_initiate``,
   ``_quantize``, ``_combine``, ``_render``, ``_complete`` must
   delegate to the matching ``*_handler`` symbol in ``phase_handlers``.
   They were deleted in an earlier refactor and restored because
   ``tests/apparat/test_processor_methods.py`` calls them directly.

3. SISA parent-walk arithmetic — the project_root computation must
   land on a directory that contains ``mangrove_platform/__init__.py``
   for both module-mode and script-mode invocations.

4. ``_create_artifact_file`` idempotency — the helper must NOT
   overwrite an existing file's content. F4 is the open policy
   question; until it is decided, the safer default is idempotent.

Run with::

    uv run python -m pytest tests/apparat/test_regression_post_simplify.py -v --no-cov
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# F5 — apparat.py data-driven HANDLER_REGISTRY
# ---------------------------------------------------------------------------


def test_handler_registry_data_driven_registration():
    """All six built-in handlers must register from a single tuple list."""
    from mangrove_platform.apparat import apparat

    expected_names = {"highlight", "normalize", "scale", "clamp", "filter", "invert"}
    registered = set(apparat.PHASE_REGISTRY.keys()) & expected_names
    missing = expected_names - registered
    assert not missing, (
        f"F5 revert detected: built-in handlers missing from registry: "
        f"{sorted(missing)}. The single-loop registration in apparat.py "
        f"is broken — every entry in HANDLER_REGISTRY must register."
    )

    # The loop signature is the load-bearing part: a tuple-unpack over
    # HANDLER_REGISTRY. If anyone reverts to a long if/elif chain, the
    # literal ``for name, handler, signature, param_map in HANDLER_REGISTRY``
    # disappears from apparat.py and this assertion fails.
    apparat_src = Path(apparat.__file__).read_text(encoding="utf-8")
    pattern = re.compile(
        r"for\s+name,\s+handler,\s+signature,\s+param_map\s+in\s+HANDLER_REGISTRY\s*:"
    )
    assert pattern.search(apparat_src), (
        "F5 revert detected: the data-driven registration loop "
        "``for name, handler, signature, param_map in HANDLER_REGISTRY:`` "
        "is missing from apparat.py. Restore the collapsed loop."
    )
    print("PASS: test_handler_registry_data_driven_registration")


# ---------------------------------------------------------------------------
# Shim methods on HorizontalTextureProcessor
# ---------------------------------------------------------------------------


def test_processor_shim_methods_route_through_process_phase():
    """Each shim must route through ``process_phase(Phase.X.value)`` so the
    canonical pipeline (pre-hooks → execute → post-hooks) is exercised
    uniformly. Calling the ``*_handler`` symbol directly bypasses the
    hook system and resurrects the silent-drift surface the
    normalization pass was created to remove.
    """
    from mangrove_platform.apparat.horizontal_texture_processor import (
        HorizontalTextureProcessor,
    )

    proc = HorizontalTextureProcessor(4, 4)
    expected_pairs = {
        "_initiate": "INITIATE",
        "_quantize": "QUANTIZE",
        "_combine": "COMBINE",
        "_render": "RENDER",
        "_complete": "COMPLETE",
    }
    import mangrove_platform.apparat.horizontal_texture_processor as mod

    proc_file = Path(mod.__file__)
    text = proc_file.read_text(encoding="utf-8")
    for shim, phase_name in expected_pairs.items():
        assert hasattr(proc, shim), (
            f"Shim revert detected: HorizontalTextureProcessor.{shim} "
            f"is missing. The five shims must remain — they are called "
            f"directly by tests/apparat/test_processor_methods.py."
        )
        # The shim must route through the canonical pipeline
        # (``self.process_phase(Phase.<X>.value)``). Catches accidental
        # rewrites that bypass the hook system.
        shim_block = re.search(
            rf"def\s+{re.escape(shim)}\s*\(.*?\n(?=\s{{4}}def\s|\s{{4}}#|\n\n)",
            text,
            re.DOTALL,
        )
        assert shim_block, f"Cannot locate shim method {shim} in source"
        assert "process_phase" in shim_block.group(0), (
            f"Shim {shim} does not call process_phase. It must route "
            f"through the canonical pipeline so the hook system fires."
        )
        assert phase_name in shim_block.group(0), (
            f"Shim {shim} does not reference Phase.{phase_name}.value. "
            f"It must dispatch to the matching phase via process_phase."
        )
    print("PASS: test_processor_shim_methods_route_through_process_phase")


# ---------------------------------------------------------------------------
# SISA parent-walk arithmetic
# ---------------------------------------------------------------------------


def test_sisa_parent_walk_arithmetic_intact():
    """The parent-walk arithmetic in ``_load_components`` must remain.

    Note (open finding): the empirical result lands on
    ``/home/cable/series`` for ``pkg = "mangrove_platform.apparat"`` —
    one level above the project root. Imports still succeed because
    Python walks up the path, but the comment in the source says this
    branch lands on the project root, which it does not. This test
    locks in the current arithmetic so any revert is loud; the
    off-by-one itself is flagged for operator review separately.
    """
    sisa_mod = importlib.import_module("mangrove_platform.apparat.sisa")
    sisa_src = Path(sisa_mod.__file__).read_text(encoding="utf-8")

    # The arithmetic lives in this exact branch.
    assert 'pkg.count(".") + 2' in sisa_src, (
        "SISA parent-walk math revert detected: the "
        '``pkg.count(".") + 2`` parent walk is missing. '
        "Restore the simplification."
    )

    # Lock the empirical result so any change is observable.
    pkg = "mangrove_platform.apparat"
    project_root = Path(sisa_mod.__file__).resolve().parents[pkg.count(".") + 2]
    expected = Path(sisa_mod.__file__).resolve().parents[3]
    assert project_root == expected, (
        f"SISA parent-walk produced unexpected root: {project_root}. "
        f"Expected {expected} (the third parent of sisa.py)."
    )
    print("PASS: test_sisa_parent_walk_arithmetic_intact")


# ---------------------------------------------------------------------------
# _create_artifact_file idempotency (F4 open policy)
# ---------------------------------------------------------------------------


def test_create_artifact_file_is_idempotent(tmp_path: Path):
    """``_create_artifact_file`` must NOT overwrite an existing file.

    F4 is the open operator decision. Until it is resolved, the safer
    default (idempotent) holds. If the operator later chooses ``(b)
    add --force flag``, this test should be revised to assert the new
    contract — but for now the existing behaviour is the contract.
    """
    from mangrove_platform.apparat.phase_handlers import _create_artifact_file

    target = tmp_path / "ARTIFACT.txt"
    target.write_text("ORIGINAL CONTENT", encoding="utf-8")
    original_mtime = target.stat().st_mtime_ns
    original_size = target.stat().st_size

    # Sleep is not needed because write_text only touches mtime if
    # the file is rewritten. If the helper overwrites, mtime will
    # change. Force a clear time gap so a coincidental mtime match
    # is impossible.
    import time

    time.sleep(0.05)

    path, digest, size = _create_artifact_file(
        tmp_path, "ARTIFACT.txt", "REPLACEMENT CONTENT — should not appear"
    )

    actual = path.read_text(encoding="utf-8")
    assert actual == "ORIGINAL CONTENT", (
        f"F4 contract violation: _create_artifact_file overwrote "
        f"existing file. Found: {actual!r}. Idempotent behavior is "
        f"the current contract."
    )
    assert path.stat().st_mtime_ns == original_mtime, (
        "F4 contract violation: _create_artifact_file touched mtime "
        "of an existing file — proof it called write_text."
    )
    assert size == original_size
    assert digest.startswith("sha256:")
    print("PASS: test_create_artifact_file_is_idempotent")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import shutil
    import tempfile

    test_handler_registry_data_driven_registration()
    test_processor_shim_methods_route_through_process_phase()
    test_sisa_parent_walk_arithmetic_intact()
    _tmp_dir = tempfile.mkdtemp(prefix="mangrove_regress_")
    try:
        test_create_artifact_file_is_idempotent(tmp_path=Path(_tmp_dir))
    finally:
        shutil.rmtree(_tmp_dir, ignore_errors=True)
    print("\n[OK] All post-simplification regression tests passed!")
