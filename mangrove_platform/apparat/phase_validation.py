from __future__ import annotations

import re

from .api import ApparatValidationError, Phase

PHASE_NAME_PATTERN = r"^[a-zA-Z0-9_]+$"
PHASE_ARG_PATTERN = r"^[a-zA-Z0-9_:,._\-+]+$"
PHASE_STEP_PATTERN = re.compile(r"^([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_,.\-+]+))?$")
PIPELINE_PATTERN = re.compile(r"^[a-zA-Z0-9_:,._\-+]+(?:/[a-zA-Z0-9_:,._\-+]+)*$")
ALLOWED_PHASES = frozenset(phase.value for phase in Phase)


def split_phase_key(phase_key: str) -> tuple[str, str | None]:
    """Split a phase expression into (name, args) without a whitelist check.

    Syntax-only parser shared by the dispatcher surface
    (``HorizontalTextureProcessor``) and the MCP gate. Unlike
    :func:`parse_phase_syntax`, it does **not** verify the name against
    :data:`ALLOWED_PHASES`, so registry-extended handlers (e.g. test-only
    ``chaos_handler``) remain dispatchable.
    """
    if not isinstance(phase_key, str):
        raise ApparatValidationError(f"Phase key must be a string, got {type(phase_key).__name__}")
    match = PHASE_STEP_PATTERN.match(phase_key)
    if not match:
        raise ApparatValidationError(
            f"Invalid phase syntax: {phase_key!r}. Expected format 'phase_name' or 'phase_name:arg1,arg2'."
        )
    name, params_str = match.groups()
    return name, params_str


def validate_phase_name(name: str) -> str:
    """Validate that a phase name is syntactically valid and allowed."""
    if not re.match(PHASE_NAME_PATTERN, name):
        raise ApparatValidationError(
            f"Invalid phase name: {name!r}. Expected alphanumeric characters and underscores only."
        )
    if name not in ALLOWED_PHASES:
        raise ApparatValidationError(f"Unknown phase: {name!r}")
    return name


def parse_phase_syntax(phase_key: str) -> tuple[str, str | None]:
    """Parse a phase expression into the phase name and optional arg string.

    Enforces both the syntax pattern and the ``ALLOWED_PHASES`` whitelist.
    """
    name, params_str = split_phase_key(phase_key)
    validate_phase_name(name)
    return name, params_str


def validate_pipeline(pipeline: str) -> str:
    """Validate a slash-separated phase pipeline string."""
    if not isinstance(pipeline, str):
        raise ApparatValidationError("Pipeline must be a string")
    if not pipeline:
        raise ApparatValidationError("Pipeline cannot be empty")
    if not PIPELINE_PATTERN.match(pipeline):
        raise ApparatValidationError(
            "Invalid pipeline syntax. Expected slash-separated phases like 'initiate/scale:2.0/complete'."
        )

    for step in pipeline.split("/"):
        if not step:
            raise ApparatValidationError("Pipeline contains an empty phase step")
        parse_phase_syntax(step)

    return pipeline
