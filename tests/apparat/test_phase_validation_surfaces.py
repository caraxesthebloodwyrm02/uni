"""Scenario-matrix regression tests for the phase/pipeline tool-call surfaces.

Pins the tailored function-call contract across the three validation surfaces:

1. ``phase_validation`` — canonical validators (``validate_phase_name``,
   ``parse_phase_syntax``, ``validate_pipeline``).
2. ``mcp.security`` — the MCP Pydantic gate (``PhaseRequest`` /
   ``PipelineRequest``), which delegates to the canonical validators.
3. ``HorizontalTextureProcessor._parse_phase_syntax`` — the dispatcher
   surface, syntax-only so registry-extended handlers remain dispatchable.

The matrix asserts all surfaces agree on a comprehensive set of phase and
pipeline strings (bare names, args, malformed syntax, whitelist misses,
case handling, and pipeline edge cases).
"""

import pytest

from mangrove_platform.apparat.api import ApparatValidationError, Phase
from mangrove_platform.apparat.horizontal_texture_processor import (
    HorizontalTextureProcessor,
)
from mangrove_platform.apparat.phase_validation import (
    parse_phase_syntax,
    split_phase_key,
    validate_phase_name,
    validate_pipeline,
)
from mangrove_platform.mcp.security import PhaseRequest, PipelineRequest


def _raises_domain_or_pydantic(call):
    with pytest.raises((ApparatValidationError, ValueError)):
        call()


def _processor_parse(phase_key):
    return HorizontalTextureProcessor(2, 2)._parse_phase_syntax(phase_key)


VALID_BARE = [p.value for p in Phase]
VALID_WITH_ARGS = [
    "scale:2.0",
    "clamp:0.1,0.9",
    "scale:-1.5",
    "scale:+2.0",
    "scale:1e3",
    "filter:alpha",
    "filter:alpha_beta",
    "filter:alpha-beta",
    "filter:alpha.beta",
    "scale:not_a_float",
]
MALFORMED = [
    "",
    " ",
    " scale",
    "scale ",
    "scale:",
    "scale:1:2",
    "scale:2.0!",
    "scale:2.0;",
    "scale:2.0 1.0",
    "!!!",
    ":arg1",
    "phase name:arg1",
    "phase:arg1 arg2",
]
UNKNOWN = ["bogus", "error_handler", "totally_made_up:1.0", "chaos_handler:runtime"]
CASE_VARIANTS = ["SCALE", "Scale"]


def test_exception_type_is_valueerror_subclass():
    """Pydantic gate and ValueError-expecting callers must both work."""
    assert issubclass(ApparatValidationError, ValueError)


def test_bare_phase_names_accepted_everywhere():
    for name in VALID_BARE:
        assert validate_phase_name(name) == name
        assert parse_phase_syntax(name) == (name, None)
        model = PhaseRequest(phase=name, width=4, height=4)
        assert model.phase == name
        assert _processor_parse(name) == (name, None)


def test_phase_with_args_accepted():
    for expr in VALID_WITH_ARGS:
        name, args = expr.split(":", 1)
        assert parse_phase_syntax(expr) == (name, args)
        model = PhaseRequest(phase=expr, width=4, height=4)
        assert model.phase == expr
        assert _processor_parse(expr) == (name, args)


def test_validate_phase_name_rejects_arg_suffix():
    """validate_phase_name is the bare-name-only contract."""
    for expr in VALID_WITH_ARGS:
        with pytest.raises(ApparatValidationError, match="Invalid phase name"):
            validate_phase_name(expr)


def test_malformed_syntax_rejected_by_all_surfaces():
    for expr in MALFORMED:
        with pytest.raises((ApparatValidationError, ValueError)):
            validate_phase_name(expr)
        with pytest.raises(ApparatValidationError, match="Invalid phase syntax"):
            parse_phase_syntax(expr)
        with pytest.raises((ApparatValidationError, ValueError)):
            PhaseRequest(phase=expr, width=4, height=4)
        with pytest.raises(ApparatValidationError, match="Invalid phase syntax"):
            _processor_parse(expr)


def test_unknown_phase_rejected_by_whitelist_surfaces():
    """Whitelist surfaces reject; the syntax-only dispatcher surface accepts."""
    for expr in UNKNOWN:
        name = expr.split(":")[0]
        with pytest.raises(ApparatValidationError, match="Unknown phase"):
            validate_phase_name(name)
        with pytest.raises(ApparatValidationError, match="Unknown phase"):
            parse_phase_syntax(expr)
        with pytest.raises((ApparatValidationError, ValueError)):
            PhaseRequest(phase=expr, width=4, height=4)
        assert _processor_parse(expr) is not None


def test_case_sensitive_whitelist():
    """Whitelist is lowercase-only; the dispatcher lowercases in process_phase."""
    for expr in CASE_VARIANTS:
        with pytest.raises(ApparatValidationError, match="Unknown phase"):
            validate_phase_name(expr)
        with pytest.raises((ApparatValidationError, ValueError)):
            PhaseRequest(phase=expr, width=4, height=4)
        assert _processor_parse(expr) == (expr, None)


def test_valid_pipelines_accepted():
    valid = [
        "initiate/scale:2.0/complete",
        "initiate/scale:2.0/clamp:0.1,0.9/complete",
    ]
    for pipeline in valid:
        assert validate_pipeline(pipeline) == pipeline
        model = PipelineRequest(pipeline=pipeline, width=4, height=4)
        assert model.pipeline == pipeline


def test_invalid_pipelines_rejected_by_both_surfaces():
    invalid = [
        "",
        " ",
        "initiate//complete",
        "/initiate",
        "initiate/",
        "scale:1:2/clamp:0.1",
        "initiate/ scale",
        "scale:2.0/complete:bad!",
    ]
    for pipeline in invalid:
        with pytest.raises((ApparatValidationError, ValueError)):
            validate_pipeline(pipeline)
        with pytest.raises((ApparatValidationError, ValueError)):
            PipelineRequest(pipeline=pipeline, width=4, height=4)


def test_processor_registry_extensions_dispatch():
    """split_phase_key keeps syntax-only parsing for non-whitelisted handlers."""
    assert split_phase_key("chaos_handler:runtime") == ("chaos_handler", "runtime")
    assert split_phase_key("chaos_handler") == ("chaos_handler", None)


def test_apparat_logic_pipeline_gate():
    """The logic surface enforces the same contract as the MCP gate."""
    from mangrove_platform.mcp import apparat_logic

    ok = apparat_logic.run_apparat_pipeline("initiate/scale:2.0/complete", 4, 4)
    assert ok["status"] == "success"
    assert ok["executed_phases"] == ["initiate", "scale:2.0", "complete"]

    bad = apparat_logic.run_apparat_pipeline("/initiate", 4, 4)
    assert bad["status"] == "error"

    empty = apparat_logic.run_apparat_pipeline("", 4, 4)
    assert empty["status"] == "error"
