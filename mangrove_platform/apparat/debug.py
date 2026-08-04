"""Developer-grade debug surface for the Apparat subsystem.

Lives next to ``apparat.py`` so handlers and LSP adapters can reach it
without a circular import. The module is intentionally side-effect free
at import time; opt-in by importing ``apa_dbg`` only when the operator
sets ``MANGROVE_APPARAT_DEBUG=1`` (or the caller invokes ``enable()``).

Public surface
--------------
- ``apa_dbg.enable()`` — turn on per-phase event capture.
- ``apa_dbg.disable()`` — turn it off and clear the buffer.
- ``apa_dbg.record(processor, phase, params, *, status="started")`` —
  push a structured event into the in-memory ring buffer.
- ``apa_dbg.dump_state(processor)`` — return a JSON-serialisable
  representation of the processor's current I/O bridge.
- ``apa_dbg.snapshot(processor)`` — alias for ``dump_state`` (shorter).
- ``apa_dbg.history()`` — return the captured event list.
- ``apa_dbg.last_error()`` — return the most recent failed event.

The events used are deliberately small keys (NOT freeform text) so they
can be grep'd and indexed by downstream tools. Event shape::

    {
        "phase": str,                          # e.g. "scale:2.0"
        "status": str,                         # "started" | "ok" | "error"
        "params": dict[str, Any],
        "elapsed_ms": float,
        "cell_count": int,
        "render_rows": int | None,
        "error": str | None,
    }
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from typing import Any

_HISTORY: list[dict[str, Any]] = []
_ENABLED: bool = os.environ.get("MANGROVE_APPARAT_DEBUG", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
_MAX_EVENTS = 256


def enable() -> None:
    """Turn on per-phase event capture from this point."""
    global _ENABLED
    _ENABLED = True


def disable() -> None:
    """Turn off event capture and clear the buffer."""
    global _ENABLED, _HISTORY
    _ENABLED = False
    _HISTORY = []


def is_enabled() -> bool:
    return _ENABLED


def _truncate() -> None:
    """Keep the in-memory ring bounded to avoid growth on long pipelines."""
    if len(_HISTORY) > _MAX_EVENTS:
        del _HISTORY[: len(_HISTORY) - _MAX_EVENTS]


def record(processor: Any, phase: str, params: dict[str, Any], *, status: str = "started") -> None:
    """Capture a single phase event.

    ``processor`` is only inspected for attribute accesses (``resolution``,
    ``ipo``); passing a mock or a partial object is fine. Errors raised
    while introspecting are downgraded to a populated ``error`` field —
    this is a debug sink, never a crash source.
    """
    if not _ENABLED:
        return
    started = time.monotonic()
    try:
        ipo = getattr(processor, "ipo", None)
        cell_count = len(ipo.input_data) if ipo is not None and ipo.input_data is not None else 0
        render_rows = (
            len(ipo.render_snapshot)
            if ipo is not None and getattr(ipo, "render_snapshot", None) is not None
            else None
        )
    except Exception as exc:  # noqa: BLE001 — debug sink absorbs everything
        event = {
            "phase": phase,
            "status": "error",
            "params": dict(params),
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
            "cell_count": 0,
            "render_rows": None,
            "error": f"introspection_failed: {exc}",
        }
    else:
        event = {
            "phase": phase,
            "status": status,
            "params": dict(params),
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
            "cell_count": cell_count,
            "render_rows": render_rows,
            "error": None,
        }
    _HISTORY.append(event)
    _truncate()


def mark_ok(phase: str, params: dict[str, Any]) -> None:
    """Record a successful completion for a previously-recorded phase."""
    if not _ENABLED or not _HISTORY:
        return
    if _HISTORY[-1]["phase"] == phase and _HISTORY[-1]["status"] == "started":
        _HISTORY[-1]["status"] = "ok"
        _HISTORY[-1]["params"] = dict(params)


def mark_error(phase: str, error: str) -> None:
    """Record a failure for a previously-recorded phase."""
    if not _ENABLED or not _HISTORY:
        return
    if _HISTORY[-1]["phase"] == phase and _HISTORY[-1]["status"] == "started":
        _HISTORY[-1]["status"] = "error"
        _HISTORY[-1]["error"] = error


def history() -> list[dict[str, Any]]:
    """Return a copy of the captured event list."""
    return list(_HISTORY)


def last_error() -> dict[str, Any] | None:
    """Return the most recent failed event, or None if there was none."""
    for event in reversed(_HISTORY):
        if event["status"] == "error":
            return event
    return None


def dump_state(processor: Any) -> dict[str, Any]:
    """Return a JSON-serialisable dump of the processor's I/O bridge.

    Intentionally narrow — exposes only the fields a developer needs to
    diagnose a phase call. Does not include the matrix cells (use
    ``history()`` for cell counts) or the branches dict (operator-curated).
    """
    ipo = getattr(processor, "ipo", None)
    if ipo is None:
        return {"error": "no ipo"}
    snapshot: dict[str, Any] = {
        "resolution": list(getattr(processor, "resolution", ())),
        "current_phase": str(getattr(processor, "current_phase", None)),
        "input_count": len(ipo.input_data) if ipo.input_data is not None else 0,
        "processed_count": len(ipo.processed_data) if ipo.processed_data is not None else 0,
        "output_count": len(ipo.output_data) if ipo.output_data is not None else 0,
        "render_rows": len(ipo.render_snapshot) if ipo.render_snapshot is not None else 0,
        "compliance_root": ipo.compliance_root,
        "history_size": len(ipo.history),
    }
    return snapshot


def to_json(obj: Any) -> str:
    """Convenience: JSON-dump a debug object with stable key ordering."""
    return json.dumps(
        obj,
        indent=2,
        sort_keys=True,
        default=lambda d: asdict(d) if hasattr(d, "__dataclass_fields__") else str(d),
    )


# Module-level alias; shorter than typing ``apparat.debug.dump_state``.
class _ApaDbg:
    enable = staticmethod(enable)
    disable = staticmethod(disable)
    is_enabled = staticmethod(is_enabled)
    record = staticmethod(record)
    mark_ok = staticmethod(mark_ok)
    mark_error = staticmethod(mark_error)
    history = staticmethod(history)
    last_error = staticmethod(last_error)
    dump_state = staticmethod(dump_state)
    snapshot = staticmethod(dump_state)
    to_json = staticmethod(to_json)


apa_dbg = _ApaDbg()
