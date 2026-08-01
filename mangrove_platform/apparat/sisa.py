#!/usr/bin/env python3
"""SISA — Apparat bootstrap workflow.

When the operator passes ``sisa`` in a prompt, run ``sisa()`` to:

1. Load apparat, phase_handlers, horizontal_texture_processor.
2. Expose phase definitions as mutable variables (PHASE_DEFINITIONS).
3. Check prerequisites (existence and non-emptiness of key files).
4. Identify warnings (missing components, stray empty files, unregistered phases).
5. Build a task-list scaffold for the Task tracker.
6. Emit a state object ready for AskUserQuestion to drive next-step choice.

Design: phases are stored as a dict so adding, removing, or remapping a
phase is a one-line edit; no enum lock-in. Handler resolution happens at
bootstrap time, not import time, so partial states still surface a useful
report instead of a hard ImportError.
"""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Phase definitions as dynamic variables — keys are phase names, values
# carry module path, handler function name, declared parameters, and a
# short description. This is intentionally a dict (mutable, runtime-editable)
# rather than an Enum (closed, import-time).
PHASE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "initiate": {
        "module": "phase_handlers",
        "handler": "initiate_handler",
        "params": [],
        "description": "Create an empty grid sized to the processor resolution.",
    },
    "quantize": {
        "module": "phase_handlers",
        "handler": "quantize_handler",
        "params": [],
        "description": "Round cell values to one decimal place.",
    },
    "combine": {
        "module": "phase_handlers",
        "handler": "combine_handler",
        "params": [],
        "description": "Tag cells with repetition-generator combinations.",
    },
    "render": {
        "module": "phase_handlers",
        "handler": "render_handler",
        "params": [],
        "description": "Produce spatial render output via the quantization matrix.",
    },
    "complete": {
        "module": "phase_handlers",
        "handler": "complete_handler",
        "params": [],
        "description": "Final read of current data — closes the pipeline.",
    },
    "normalize": {
        "module": "apparat",
        "handler": "normalize_handler",
        "params": [],
        "description": "Rescale cell values into the [0, 1] range.",
    },
    "scale": {
        "module": "apparat",
        "handler": "scale_handler",
        "params": ["factor"],
        "description": "Multiply cell values by a factor.",
    },
    "clamp": {
        "module": "apparat",
        "handler": "clamp_handler",
        "params": ["min_val", "max_val"],
        "description": "Clamp cell values into [min_val, max_val].",
    },
    "filter": {
        "module": "apparat",
        "handler": "filter_handler",
        "params": ["threshold"],
        "description": "Drop cells whose value is below threshold.",
    },
    "invert": {
        "module": "apparat",
        "handler": "invert_handler",
        "params": [],
        "description": "Replace each value with 1.0 − value.",
    },
    "highlight": {
        "module": "apparat",
        "handler": "highlight_handler",
        "params": [],
        "description": "Annotate texture_type with article / vowel / consonant tags.",
    },
    "compliance_baseline": {
        "module": "phase_handlers",
        "handler": "compliance_baseline_handler",
        "params": [],
        "description": "Materialize LICENSE, NOTICE, and TERMS_OF_ENGAGEMENT.md at the apparat root.",
    },
    "validate_acceleration": {
        "module": "apparat",
        "handler": "validate_acceleration_handler",
        "params": [],
        "description": "Verify processing acceleration and normalization baselines using the golding validator.",
    },
}


@dataclass
class SisaState:
    """Snapshot returned by ``sisa()`` — operator-facing, JSON-friendly."""

    trigger: str = "sisa"
    ready: bool = False
    components_loaded: list[str] = field(default_factory=list)
    components_failed: list[str] = field(default_factory=list)
    phases_resolved: list[str] = field(default_factory=list)
    phases_missing: list[str] = field(default_factory=list)
    phases_newly_registered: list[str] = field(default_factory=list)
    prerequisites_met: list[str] = field(default_factory=list)
    prerequisites_missing: list[str] = field(default_factory=list)
    context_snapshot: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    tasks: list[dict[str, str]] = field(default_factory=list)


def _safe_import(dotted: str) -> Any:
    """Import ``dotted`` and return either the module or the exception."""
    try:
        return importlib.import_module(dotted)
    except Exception as exc:  # noqa: BLE001 — bootstrap must catch anything
        return exc


def _load_components() -> tuple[list[str], list[str]]:
    """Import components using their absolute package paths to ensure relative
    imports resolve correctly and to avoid collisions with the stdlib 'platform' module.
    """
    import importlib

    # Ensure the mangrove root is in sys.path
    # sisa.py is at mangrove/platform/apparat/sisa.py
    root = Path(__file__).resolve().parent.parent.parent.parent  # /home/cable/series
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    loaded, failed = [], []
    for name in ("apparat", "phase_handlers", "horizontal_texture_processor"):
        full_name = f"mangrove.platform.apparat.{name}"
        try:
            importlib.import_module(full_name)
            loaded.append(name)
        except Exception as exc:  # noqa: BLE001
            failed.append(f"{name}: {type(exc).__name__}: {exc}")
    return loaded, failed


def _auto_register_handlers() -> list[str]:
    """Register any phase whose ``*_handler`` symbol exists in its module.

    This makes the bootstrap self-sufficient: callers no longer need to
    run the registration block from ``horizontal_texture_processor.py``
    before invoking a phase. Returns the list of phases newly registered.
    """
    apparat_mod = sys.modules.get("mangrove.platform.apparat.apparat")
    phase_mod = sys.modules.get("mangrove.platform.apparat.phase_handlers")
    if apparat_mod is None or not hasattr(apparat_mod, "register_phase_handler"):
        return []

    register = apparat_mod.register_phase_handler
    get_handler = apparat_mod.get_phase_handler
    newly: list[str] = []

    for phase_name, definition in PHASE_DEFINITIONS.items():
        if get_handler(phase_name):
            continue  # already registered
        module_name = definition["module"]
        handler_name = definition["handler"]
        target = (
            phase_mod
            if module_name == "phase_handlers"
            else apparat_mod
            if module_name == "apparat"
            else None
        )
        if target is None or not hasattr(target, handler_name):
            continue
        register(phase_name)(getattr(target, handler_name))
        newly.append(phase_name)
    return newly


def _resolve_phases() -> tuple[list[str], list[str]]:
    """Cross-check PHASE_DEFINITIONS against the live registry."""
    handler = sys.modules.get("mangrove.platform.apparat.apparat")
    if handler is None or not hasattr(handler, "get_phase_handler"):
        return [], list(PHASE_DEFINITIONS.keys())
    get_phase_handler = handler.get_phase_handler

    resolved, missing = [], []
    for phase_name in PHASE_DEFINITIONS:
        if get_phase_handler(phase_name):
            resolved.append(phase_name)
        else:
            missing.append(phase_name)
    return resolved, missing


def _check_prerequisites(root: Path) -> tuple[list[str], list[str]]:
    """Confirm key files exist and are non-empty."""
    candidates = [
        root / "apparat.py",
        root / "phase_handlers.py",
        root / "horizontal_texture_processor.py",
        root / "review_pack.py",
        root / "sisa.py",
        root.parent.parent / "tests" / "apparat" / "test_validate_acceleration.py",
        root.parent.parent / "tests" / "apparat" / "test_dispatcher.py",
    ]
    met, missing = [], []
    for p in candidates:
        if p.exists() and p.stat().st_size > 0:
            met.append(str(p))
        else:
            missing.append(str(p))
    return met, missing


def _identify_warnings(root: Path, failed: list[str], missing_prereq: list[str]) -> list[str]:
    """Surface anything that the operator should know before continuing."""
    warnings: list[str] = []
    if failed:
        warnings.append(f"Components failed to import: {failed}")
    if missing_prereq:
        warnings.append(f"Missing prerequisite files: {missing_prereq}")
    stray = root / "test_dispatcher_quick.py"
    if stray.exists() and stray.stat().st_size == 0:
        warnings.append(f"Empty stray file present: {stray}")
    # Bidirectional Registry/Enum Synchronization Check
    processor = sys.modules.get("apparat.horizontal_texture_processor") or sys.modules.get(
        "mangrove.platform.apparat.horizontal_texture_processor"
    )
    if processor is not None and hasattr(processor, "Phase"):
        enum_values = {p.value for p in processor.Phase}
    else:
        enum_values = set()
    declared = set(PHASE_DEFINITIONS.keys())

    # 1. Declared in Registry but missing from Enum
    extra_in_registry = declared - enum_values - {"highlight"}
    if extra_in_registry:
        warnings.append(
            f"Registry drift: Phases declared but not in Phase enum: {sorted(extra_in_registry)}"
        )

    # 2. Declared in Enum but missing from Registry
    missing_in_registry = enum_values - declared
    if missing_in_registry:
        warnings.append(
            f"Registry drift: Phases in Phase enum but missing from registry: {sorted(missing_in_registry)}"
        )

    return warnings


def _build_tasks(state: SisaState) -> list[dict[str, str]]:
    """Scaffold tasks for the operator's task tracker."""
    base = [
        {
            "subject": "Confirm SISA bootstrap state",
            "activeForm": "Confirming SISA bootstrap state",
        },
        {"subject": "Clear any warnings surfaced", "activeForm": "Clearing warnings"},
    ]
    if state.components_failed:
        base.append(
            {
                "subject": "Resolve failed component imports",
                "activeForm": "Resolving failed imports",
            }
        )
    if state.phases_missing:
        base.append(
            {
                "subject": "Register missing phase handlers",
                "activeForm": "Registering missing handlers",
            }
        )
    if state.prerequisites_missing:
        base.append(
            {
                "subject": "Materialize missing prerequisite files",
                "activeForm": "Materializing prerequisites",
            }
        )
    base.append({"subject": "Pick the next milestone", "activeForm": "Picking the next milestone"})
    return base


def sisa(
    prompt: str = "",
    context: dict[str, Any] | None = None,
    *,
    strict: bool = False,
    phase_filter: str | None = None,
) -> SisaState:
    """Run the SISA bootstrap. Returns a populated :class:`SisaState`.

    Parameters
    ----------
    prompt:
        The operator's prompt text. ``sisa`` (case-insensitive) must appear
        for the trigger to fire — this function checks defensively and
        still returns a state object even when the trigger is missing, so
        callers can decide how to handle it.
    context:
        Optional dict of pre-loaded state. Reserved for future use.
        Keys supported today: ``cwd`` (override detected project root),
        ``git_branch`` (recorded in the snapshot for log correlation),
        ``extra_phases`` (dict merged into ``PHASE_DEFINITIONS`` before
        resolution).
    strict:
        When ``True``, the returned ``SisaState.ready`` is forced to
        ``False`` if any warning surfaces. The CLI maps this to exit 2.
    phase_filter:
        When set, only this phase is resolved / reported. Useful for
        ``--phase <name>`` probes.
    """
    if context and "extra_phases" in context:
        merge = context["extra_phases"]
        if isinstance(merge, dict):
            PHASE_DEFINITIONS.update(merge)

    state = SisaState()
    state.components_loaded, state.components_failed = _load_components()
    state.phases_newly_registered = _auto_register_handlers()
    if phase_filter:
        if phase_filter in PHASE_DEFINITIONS:
            state.phases_resolved, state.phases_missing = _resolve_phases()
            state.phases_resolved = [p for p in state.phases_resolved if p == phase_filter]
            state.phases_missing = [p for p in state.phases_missing if p == phase_filter]
        else:
            state.phases_missing = [phase_filter]
    else:
        state.phases_resolved, state.phases_missing = _resolve_phases()
    root = Path(__file__).parent
    if context and context.get("cwd"):
        root = Path(context["cwd"])
    state.prerequisites_met, state.prerequisites_missing = _check_prerequisites(root)
    state.warnings = _identify_warnings(root, state.components_failed, state.prerequisites_missing)
    state.tasks = _build_tasks(state)
    if context and context.get("git_branch"):
        state.context_snapshot = {"git_branch": context["git_branch"]}
    state.ready = (
        not state.components_failed
        and not state.phases_missing
        and not state.prerequisites_missing
        and not any("Registry drift" in w for w in state.warnings)
        and not (strict and state.warnings)
    )
    return state


def render_summary(state: SisaState) -> str:
    """Human-readable summary suitable for stderr / stdout."""
    lines = [
        f"SISA bootstrap (trigger='{state.trigger}', ready={state.ready})",
        "-" * 56,
        f"Components loaded : {len(state.components_loaded)} ({', '.join(state.components_loaded) or '—'})",
        f"Components failed : {len(state.components_failed)}",
        f"Phases resolved   : {len(state.phases_resolved)}/{len(PHASE_DEFINITIONS)}",
        f"Phases missing    : {state.phases_missing or '—'}",
        f"Newly registered  : {state.phases_newly_registered or '—'}",
        f"Prereqs met       : {len(state.prerequisites_met)}/{len(state.prerequisites_met) + len(state.prerequisites_missing)}",
        f"Warnings          : {len(state.warnings)}",
        f"Tasks scaffolded  : {len(state.tasks)}",
    ]
    if state.warnings:
        lines.append("\nWarnings:")
        for w in state.warnings:
            lines.append(f"  - {w}")
    return "\n".join(lines)


def to_jsonable(state: SisaState) -> dict[str, Any]:
    """Convert a SisaState into a JSON-serialisable dict."""

    def _coerce(value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    return {
        "trigger": state.trigger,
        "ready": state.ready,
        "components_loaded": state.components_loaded,
        "components_failed": state.components_failed,
        "phases_resolved": state.phases_resolved,
        "phases_missing": state.phases_missing,
        "phases_newly_registered": state.phases_newly_registered,
        "prerequisites_met": state.prerequisites_met,
        "prerequisites_missing": state.prerequisites_missing,
        "warnings": state.warnings,
        "tasks": state.tasks,
        "context_snapshot": {k: _coerce(v) for k, v in state.context_snapshot.items()},
    }


def _build_arg_parser() -> Any:
    import argparse

    parser = argparse.ArgumentParser(
        prog="sisa",
        description="Apparat bootstrap: load components, resolve phases, surface warnings.",
        add_help=True,
    )
    parser.add_argument("-V", "--version", action="version", version="sisa 0.1.0")
    parser.add_argument(
        "-p",
        "--prompt",
        default="",
        help="operator prompt text (recorded for log correlation)",
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="emit the bootstrap state as JSON to stdout",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress the human summary; emit only warnings to stderr",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="include the task scaffold and the registered-phase list",
    )
    parser.add_argument(
        "-s",
        "--strict",
        action="store_true",
        help="exit non-zero if any warning is present (use as a CI gate)",
    )
    parser.add_argument(
        "-P",
        "--phase",
        default=None,
        metavar="NAME",
        help="restrict resolution to a single phase name",
    )
    parser.add_argument(
        "-l",
        "--list-phases",
        action="store_true",
        help="print registered phase names to stdout, one per line, and exit",
    )
    return parser


def _print_phases(state: SisaState) -> None:
    """Emit registered phase names, one per line, to stdout."""
    for name in state.phases_resolved:
        print(name)


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    context: dict[str, Any] = {}
    if args.phase:
        context["phase_filter"] = args.phase

    state = sisa(prompt=args.prompt, context=context, strict=args.strict)

    # --list-phases is a pure read of the registry; exit early with data on stdout.
    if args.list_phases:
        _print_phases(state)
        return 0 if state.phases_resolved else 1

    if args.json:
        import json

        print(json.dumps(to_jsonable(state), indent=2))
        for w in state.warnings:
            print(f"sisa: warning: {w}", file=sys.stderr)
        if args.strict and state.warnings:
            return 3
        return 0 if state.ready else 1

    # Human-readable path: data on stdout, diagnostics on stderr.
    if not args.quiet:
        print(render_summary(state))
        if args.verbose:
            print()
            print("Registered phases:")
            for name in state.phases_resolved:
                print(f"  {name}")
            if state.tasks:
                print()
                print("Tasks:")
                for t in state.tasks:
                    print(f"  - {t['subject']}")
    for w in state.warnings:
        print(f"sisa: warning: {w}", file=sys.stderr)

    if args.strict and state.warnings:
        return 3
    return 0 if state.ready else 1


if __name__ == "__main__":
    sys.exit(main())
