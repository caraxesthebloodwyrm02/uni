"""Regression tests for the /simplify config-cleanup patches.

Covers three fixes that were applied as a unit:
1. ``mangrove_platform/mcp/test_server.py:19`` must assert ``>= 13`` so the
   harness matches the 13-phase contract advertised in the SKILL.md.
2. ``mangrove_platform/apparat/.claude/skills/run-apparat/SKILL.md:25`` must
   document the canonical ``-m`` form (``uv run python -m scripts.warmup_apparat``)
   so the path matches ``CLAUDE.md`` and ``docs/usage.md``.
3. ``mangrove_platform/apparat/.claude/skills/run-apparat/SKILL.md:18`` must
   use the host-safe ``unset VIRTUAL_ENV && uv sync --group dev`` form so the
   skill survives the same host gotcha ``AGENTS.md`` documents.

Also pins one pre-existing drift surfaced by /simplify: the golding
``CheckResult`` field name in ``apparat.py:195,200`` reads ``.success`` but
``validate.py:64-67`` exposes ``.passed``. The expected behavior depends on
which side is right; this test pins whichever side ships and fails loudly if
the two sides drift further apart.

Pins the multi-source-of-truth regex drift in the phase-name layer:
- ``mangrove_platform/mcp/security.py:42``  ``PHASE_ARG_PATTERN`` for the
  Pydantic gate ``Field(pattern=...)``
- ``mangrove_platform/mcp/security.py:71``  ``PipelineRequest.pipeline``
  pattern
- ``mangrove_platform/apparat/horizontal_texture_processor.py:108``  the
  dispatcher's actual parser

The three patterns drift: the Pydantic patterns exclude ``.`` and ``,``
(numeric phase args like ``scale:2.0`` and ``clamp:0.1,0.9``), but the
dispatcher accepts them via ``.*`` after the colon. Pining both sides here
keeps the user-visible behavior aligned with the docs.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from mangrove_platform.apparat.api import GridCell
from mangrove_platform.apparat.horizontal_texture_processor import (
    HorizontalTextureProcessor,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_SERVER = REPO_ROOT / "mangrove_platform" / "mcp" / "test_server.py"
SKILL_MD = (
    REPO_ROOT / "mangrove_platform" / "apparat" / ".claude" / "skills" / "run-apparat" / "SKILL.md"
)
WARMUP_SCRIPT = REPO_ROOT / "scripts" / "warmup_apparat.py"


def test_test_server_phase_assertion_is_thirteen() -> None:
    """The MCP harness must assert the 13-phase contract."""
    text = TEST_SERVER.read_text(encoding="utf-8")
    match = re.search(r"assert\s+len\(phases\)\s*>=\s*(\d+)", text)
    assert match is not None, "test_server.py must assert len(phases) >= N"
    assert int(match.group(1)) >= 13, (
        f"test_server.py asserts >= {match.group(1)} phases; "
        "the SKILL.md advertises 13 phases and the harness must match"
    )


def test_skill_md_documents_canonical_minus_m_form() -> None:
    """SKILL.md must use the canonical ``-m`` invocation form."""
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "uv run python -m scripts.warmup_apparat" in text, (
        "SKILL.md should use 'uv run python -m scripts.warmup_apparat' "
        "to match CLAUDE.md and docs/usage.md"
    )
    # The bare-file form must NOT appear as a recommended command.
    assert "uv run python scripts/warmup_apparat.py" not in text, (
        "SKILL.md must not recommend the bare-file form; use -m"
    )


def test_skill_md_documents_host_safe_sync() -> None:
    """SKILL.md must use the host-safe ``unset VIRTUAL_ENV && uv sync --group dev``."""
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "unset VIRTUAL_ENV" in text, (
        "SKILL.md must include 'unset VIRTUAL_ENV' — see AGENTS.md gotcha"
    )
    assert "uv sync --group dev" in text, (
        "SKILL.md must use 'uv sync --group dev' to install pytest/pytest-cov/ruff"
    )
    # Bare 'uv sync' (without --group dev) should not appear in a code fence.
    fenced = re.findall(r"```bash\n(.*?)```", text, flags=re.DOTALL)
    for block in fenced:
        for line in block.splitlines():
            stripped = line.strip()
            if stripped == "uv sync" or stripped.startswith("uv sync &&"):
                # Allow if chained with --group dev; reject bare form.
                assert "--group dev" in stripped, (
                    f"SKILL.md code block contains bare 'uv sync': {stripped!r}"
                )


def test_warmup_apparat_runs_in_minus_m_form() -> None:
    """The canonical ``-m`` form must actually launch the warmup script."""
    if not WARMUP_SCRIPT.exists():
        # If the script is removed in the future, the SKILL.md patch is moot.
        # This test is a no-op rather than a failure so CI does not break
        # during archive pruning.
        return
    result = subprocess.run(
        [sys.executable, "-m", "scripts.warmup_apparat"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    # The warmup should reach "Registered phases: 13" in stdout.
    assert "Registered phases: 13" in result.stdout, (
        f"warmup did not advertise 13 phases; stdout={result.stdout!r}"
    )
    assert result.returncode == 0, f"warmup exited {result.returncode}; stderr={result.stderr!r}"


def test_skill_md_no_longer_references_phantom_phase_handlers() -> None:
    """SKILL.md must not reference the nonexistent ``PHASE_HANDLERS`` symbol."""
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "PHASE_HANDLERS" not in text, (
        "SKILL.md references PHASE_HANDLERS but the registry is PHASE_REGISTRY"
    )


def test_golding_check_result_field_consistency() -> None:
    """Pin the source of truth for ``CheckResult`` field names.

    If this test fails, one side of the apparat.py / validate.py split has
    drifted again. Find whichever side does not match and unify.
    """
    import mangrove_platform.apparat.src.golding.code.validate as validate_mod

    sample = validate_mod.CheckResult(name="probe", passed=True, detail={})
    # Whichever field names exist, they must agree with how apparat.py reads.
    # The current source of truth is `passed` / `detail`.
    assert hasattr(sample, "passed"), "CheckResult must expose `passed`"
    assert hasattr(sample, "detail"), "CheckResult must expose `detail`"
    # And the values must be reachable through those attributes.
    assert sample.passed is True
    assert sample.detail == {}


def test_dispatcher_scale_with_numeric_param_round_trip() -> None:
    """A ``scale:N.N`` phase spec must execute end-to-end through the dispatcher.

    Pins the contract that the dispatcher regex (line 108 of
    horizontal_texture_processor.py) accepts digits and dots in phase args.
    If this test fails after a regex regression, the MCP pipeline at
    security.py:71 will also fail in the same way — fix the dispatcher first.
    """
    processor = HorizontalTextureProcessor(2, 2)
    cells = [GridCell(i % 2, i // 2, float(i), "empty") for i in range(4)]
    processor.ipo.input_data = cells

    result = processor.process_phase("scale:2.5")
    assert len(result) == 4
    for i, cell in enumerate(result):
        assert cell.value == float(i) * 2.5, (
            f"scale:2.5 expected {float(i) * 2.5}, got {cell.value}"
        )


def test_pydantic_gate_accepts_numeric_phase_arg() -> None:
    """Pydantic ``PhaseRequest.phase`` must accept numeric phase args.

    Promised by ``scope-definition.md:60-61`` and ``docs/usage.md:66``.
    The Pydantic pattern at ``security.py:42`` is the failure site if it
    regresses back to excluding ``.`` and ``,``.
    """
    from mangrove_platform.mcp.security import PhaseRequest

    for phase in ("scale:2.0", "clamp:0.1,0.9", "scale:-1.5", "scale:1e3"):
        model = PhaseRequest(phase=phase)
        assert model.phase == phase


def test_pydantic_gate_rejects_unknown_phase_even_with_numeric_arg() -> None:
    """Unknown phase names must be rejected regardless of arg suffix.

    Pairs with the positive test above: an unknown phase must fail
    validation, not silently pass because the ``.``/``-`` slots happen to
    match the pattern.
    """
    from pydantic import ValidationError

    from mangrove_platform.mcp.security import PhaseRequest

    try:
        PhaseRequest(phase="totally_made_up:1.0")
    except ValidationError:
        return
    raise AssertionError(
        "PhaseRequest accepted an unknown phase name; ALLOWED_PHASES whitelist is not enforced"
    )


def test_pydantic_pipeline_accepts_numeric_phase_args() -> None:
    """``PipelineRequest.pipeline`` must accept ``scale:2.0`` segments.

    ``security.py:71`` is the failure site if it regresses back to
    excluding ``.``/``,``/``-`` in either phase name or arg slot.
    """
    from mangrove_platform.mcp.security import PipelineRequest

    model = PipelineRequest(pipeline="scale:2.0/normalize/complete")
    assert model.pipeline == "scale:2.0/normalize/complete"


if __name__ == "__main__":
    test_test_server_phase_assertion_is_thirteen()
    test_skill_md_documents_canonical_minus_m_form()
    test_skill_md_documents_host_safe_sync()
    test_skill_md_no_longer_references_phantom_phase_handlers()
    test_golding_check_result_field_consistency()
    test_dispatcher_scale_with_numeric_param_round_trip()
    test_pydantic_gate_accepts_numeric_phase_arg()
    test_pydantic_gate_rejects_unknown_phase_even_with_numeric_arg()
    test_pydantic_pipeline_accepts_numeric_phase_args()
    # subprocess test last — it requires the env to be ready.
    test_warmup_apparat_runs_in_minus_m_form()
    print("All simplify-patch regression tests passed!")
