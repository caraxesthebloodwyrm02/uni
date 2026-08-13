"""Regression tests for the MCP audit-logging fix.

The audit-logging layer (``mangrove_platform/mcp/security.py:log_tool_invocation``)
exists to observe every invocation of the Apparat MCP tools. A code review
in 2026-08-04 found that the rate-limit rejection path and the validation-
failure path inside ``_gate`` were early-returning *before* the audit log
was emitted, so abusive callers — exactly the population the ``RateLimiter``
was meant to monitor — were silently unrecorded.

These tests read ``apparat_server.py`` as source and assert that ``_gate``
still calls ``log_tool_invocation`` on both rejection branches. The test
style (read source, assert literal presence) matches the existing apparat
regression tests in ``tests/apparat/test_regression_post_simplify.py``.

Run with::

    uv run python -m pytest tests/test_mcp_audit_logging.py -v --no-cov
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APPARAT_SERVER_SRC = (REPO_ROOT / "mangrove_platform" / "mcp" / "apparat_server.py").read_text(
    encoding="utf-8"
)
SECURITY_SRC = (REPO_ROOT / "mangrove_platform" / "mcp" / "security.py").read_text(encoding="utf-8")


def _gate_body(src: str) -> str:
    """Return the body of the ``_gate`` function in ``apparat_server.py``.

    Matches from ``def _gate(`` until the next ``def `` or ``class `` block,
    or end-of-file. The regex is intentionally permissive: ``_gate`` is the
    only function in this file that should look like it, and we only assert
    on call-count, not on its surrounding structure.
    """
    match = re.search(r"def _gate\(.*?(?=\n\ndef |\nclass |\Z)", src, re.DOTALL)
    assert match, "_gate function not found in apparat_server.py"
    return match.group(0)


def test_gate_audits_rate_limit_rejection():
    """_gate MUST log every rate-limit rejection via log_tool_invocation.

    The previous implementation returned silently from the rejection branch
    and the abusive callers the ``RateLimiter`` was meant to observe were
    unrecorded. The status string ``"rate_limited"`` distinguishes this
    audit entry from success-path audits emitted by the tool handlers.
    """
    body = _gate_body(APPARAT_SERVER_SRC)
    # Find the rejection branch and assert an audit call sits inside it.
    rejection_branch = re.search(
        r"if not allowed:.*?(?=\n    \S|\Z)",
        body,
        re.DOTALL,
    )
    assert rejection_branch, "rate-limit rejection branch not found in _gate"
    branch = rejection_branch.group(0)
    assert "log_tool_invocation" in branch, (
        "Audit gap: rate-limit rejection branch of _gate does not call "
        "log_tool_invocation. Abusive callers are silently unrecorded."
    )
    assert '"rate_limited"' in branch, (
        "Audit gap: rate-limit rejection branch must use status="
        '"rate_limited" so log consumers can grep for it.'
    )
    print("PASS: test_gate_audits_rate_limit_rejection")


def test_gate_audits_validation_failure():
    """_gate MUST log validation failures via log_tool_invocation.

    ``validate_request`` returns ``{\"status\": \"error\", ...}`` on bad input.
    Before the fix, the tool handlers early-returned on that shape without
    ever calling ``log_tool_invocation``. The gate now records these with
    status ``"validation_failed"``.
    """
    body = _gate_body(APPARAT_SERVER_SRC)
    assert 'log_tool_invocation(tool_name, params, "validation_failed"' in body, (
        "Audit gap: _gate does not call log_tool_invocation with status="
        '"validation_failed" when validate_request fails. The gate body '
        "should contain exactly: "
        'log_tool_invocation(tool_name, params, "validation_failed", '
        'detail=result.get("error", ""))'
    )
    print("PASS: test_gate_audits_validation_failure")


def test_get_apparat_state_audits_validation_failures():
    """``get_apparat_state`` calls ``validate_request`` directly (not via ``_gate``).

    Without an explicit audit call on the validation-failure branch, validation
    errors against this tool were silently dropped. This test locks the
    pre-fix removal in place.
    """
    src = APPARAT_SERVER_SRC
    # Match the get_apparat_state handler body.
    handler = re.search(
        r"def get_apparat_state\(.*?(?=\n\n@mcp\.tool|\n\ndef |\Z)",
        src,
        re.DOTALL,
    )
    assert handler, "get_apparat_state handler not found"
    body = handler.group(0)
    # The handler must log validation_failed before returning the error.
    assert "validation_failed" in body, (
        "Audit gap: get_apparat_state does not emit a log_tool_invocation "
        "entry with status='validation_failed' on bad input. "
        "This tool calls validate_request directly (bypassing _gate), "
        "so it owns its own audit log."
    )
    print("PASS: test_get_apparat_state_audits_validation_failures")


def test_get_apparat_state_uses_isinstance_for_validation_failure():
    """``get_apparat_state`` MUST discriminate `_ErrorResult` via `isinstance`.

    Background: a 2026-08-04 code review found that the validation-failure
    branch in ``get_apparat_state`` was calling ``validated.get("status")`` on
    a ``_ValidationFailedResult`` dataclass, which raises ``AttributeError``
    (dataclasses have no ``.get`` method). The MCP caller received an
    unhelpful internal error instead of the structured error payload.

    This test asserts the handler uses ``isinstance(validated, _ErrorResult)``
    for discrimination, which is the only correct shape because
    ``validate_request`` returns either ``dict`` (success) or a dataclass
    instance (failure).
    """
    src = APPARAT_SERVER_SRC
    handler = re.search(
        r"def get_apparat_state\(.*?(?=\n\n@mcp\.tool|\n\ndef |\Z)",
        src,
        re.DOTALL,
    )
    assert handler, "get_apparat_state handler not found"
    body = handler.group(0)
    assert "isinstance(validated, _ErrorResult)" in body, (
        "Regression: get_apparat_state must check `isinstance(validated, _ErrorResult)` "
        "to discriminate the validation-failure branch. The previous "
        '`validated.get("status") == "error"` pattern raised AttributeError '
        "because _ValidationFailedResult is a dataclass, not a dict."
    )
    assert 'validated.get("status")' not in body, (
        'Regression: get_apparat_state still uses `validated.get("status")` '
        "somewhere. That call crashes with AttributeError on validation "
        "failure because validate_request returns a _ValidationFailedResult "
        "dataclass, not a dict."
    )
    print("PASS: test_get_apparat_state_uses_isinstance_for_validation_failure")


def test_bypass_tools_emit_structured_audit():
    """``check_apparat_health`` and ``list_apparat_phases`` MUST use the
    structured ``log_tool_invocation`` entry point rather than ``logger.info``.

    These tools bypass ``_gate`` (read-only, no input). Before the fix they
    emitted only ``logger.info('<tool_name> invoked')``. The audit layer
    needs a structured entry for grep-ability from ``~/.echoes/audit.ndjson``.
    """
    src = APPARAT_SERVER_SRC
    for tool_name in ("check_apparat_health", "list_apparat_phases"):
        handler = re.search(
            rf"def {tool_name}\(.*?(?=\n\n@mcp\.tool|\n\ndef |\Z)",
            src,
            re.DOTALL,
        )
        assert handler, f"{tool_name} handler not found in apparat_server.py"
        body = handler.group(0)
        assert "log_tool_invocation" in body, (
            f"Audit gap: {tool_name} does not call log_tool_invocation. "
            "Bypass tools must still emit a structured audit entry."
        )
        # Sanity: the literal tool name should appear in the audit call.
        assert f'log_tool_invocation("{tool_name}"' in body, (
            f"{tool_name} audit call does not match its handler name. "
            "Audit consumer filtering by tool name would misroute this entry."
        )
    print("PASS: test_bypass_tools_emit_structured_audit")


def test_internal_error_result_dataclasses_exist():
    """``_ErrorResult``, ``_RateLimitedResult``, ``_ValidationFailedResult`` must exist.

    These are the internal-stepping-stone dataclasses that the refactor
    introduced. ``_RateLimitedResult`` must be a frozen subclass of
    ``_ErrorResult`` and must carry a ``retry_after_seconds`` field. ``_ValidationFailedResult``
    must be a frozen subclass of ``_ErrorResult`` with no extra fields.
    """
    # _ErrorResult: base class with one field `error: str`.
    assert re.search(
        r"@dataclass\(frozen=True\)\s+class _ErrorResult:",
        SECURITY_SRC,
    ), "@dataclass(frozen=True) class _ErrorResult: not found in security.py"
    assert "    error: str" in SECURITY_SRC, "_ErrorResult must declare `error: str`"

    # _RateLimitedResult: subclass with `retry_after_seconds: float`.
    assert re.search(
        r"class _RateLimitedResult\(_ErrorResult\):",
        SECURITY_SRC,
    ), "_RateLimitedResult must inherit from _ErrorResult"
    assert re.search(
        r"class _RateLimitedResult\(_ErrorResult\):.*?retry_after_seconds:\s*float",
        SECURITY_SRC,
        re.DOTALL,
    ), "_RateLimitedResult must declare `retry_after_seconds: float`"

    # _ValidationFailedResult: subclass with no extra fields beyond `error`.
    assert re.search(
        r"class _ValidationFailedResult\(_ErrorResult\):",
        SECURITY_SRC,
    ), "_ValidationFailedResult must inherit from _ErrorResult"
    # The body of _ValidationFailedResult between the class header and the next
    # class header or end-of-file must contain only a docstring (no field declarations).
    match = re.search(
        r"class _ValidationFailedResult\(_ErrorResult\):(.*?)(?=\nclass |\Z)",
        SECURITY_SRC,
        re.DOTALL,
    )
    assert match, "_ValidationFailedResult body not found"
    body = match.group(1)
    assert "retry_after_seconds" not in body, (
        "_ValidationFailedResult must NOT carry retry_after_seconds — "
        "that field is rate-limiter-specific and would dilute the type."
    )
    assert "status:" not in body, (
        "_ValidationFailedResult must NOT carry a `status` field — "
        "the wire-format status is built explicitly in _gate."
    )
    print("PASS: test_internal_error_result_dataclasses_exist")


def test_gate_uses_dataclass_for_rate_limit_branch():
    """The rate-limit branch in ``_gate`` must construct a :class:`_RateLimitedResult`.

    The audit-detail field (``detail=result.error``) is a dataclass attribute
    access, not a dict lookup. This locks the dataclass refactor in place.
    """
    body = _gate_body(APPARAT_SERVER_SRC)
    rejection_branch = re.search(
        r"if not allowed:.*?(?=\n    \S|\Z)",
        body,
        re.DOTALL,
    )
    assert rejection_branch, "rate-limit rejection branch not found in _gate"
    branch = rejection_branch.group(0)
    assert "_RateLimitedResult(" in branch, (
        "rate-limit rejection branch must construct _RateLimitedResult(...). "
        "The dataclass carries retry_after_seconds as a typed field."
    )
    assert "detail=result.error" in branch, (
        "rate-limit audit call must read detail from result.error "
        "(dataclass attribute access), not result.get('error', '')."
    )
    print("PASS: test_gate_uses_dataclass_for_rate_limit_branch")


if __name__ == "__main__":
    test_gate_audits_rate_limit_rejection()
    test_gate_audits_validation_failure()
    test_get_apparat_state_audits_validation_failures()
    test_get_apparat_state_uses_isinstance_for_validation_failure()
    test_bypass_tools_emit_structured_audit()
    test_internal_error_result_dataclasses_exist()
    test_gate_uses_dataclass_for_rate_limit_branch()
    print("\n[OK] All MCP audit-logging regression tests passed!")
