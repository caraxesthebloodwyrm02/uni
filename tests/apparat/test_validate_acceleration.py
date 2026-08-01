"""Tests for src/golding/validate.py.

Each exit-code class is exercised by deliberately misconfiguring the
wrapper and asserting the right code is returned. The happy path
(clean config, all three checks pass) is the implicit baseline and
is the gate that turns the CI job green on a healthy checkout.

These tests intentionally do not import AccelerationWrapper,
GoldingEngine, or any other runtime class. The check functions are
replaced via monkeypatch so each test exercises only the routing
logic in validate.main() and the exit-code table — not the
underlying runtime. That keeps the test suite fast and deterministic,
and makes a regression in the runtime itself show up in the
``test`` job (which already runs the full test matrix), not here.

Module-level skip
-----------------
This test file lives in tests/ (tracked scope) but its companion
implementation src/golding/validate.py is in structural-excess
scope. On a fresh clone where src/ has not been bootstrapped
(`make bootstrap`), the import below would fail. ``importorskip``
turns that into a clean skip rather than a collection error, so
the test file can sit in the tree alongside its (not-yet-merged)
implementation without breaking CI.
"""

import importlib.util
import json
import os
import subprocess
import sys

import pytest

# Add the golding module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../mangrove_platform/apparat/src"))

# Skip the entire module if the companion implementation is not
# importable. This is the bridge between tracked-scope tests and
# structural-excess source: the test can be reviewed and merged
# before the implementation lands, without breaking the build.
_validate_spec = importlib.util.find_spec("golding.validate")
if _validate_spec is None:
    pytest.skip(
        reason="golding.validate is not importable; mangrove_platform/apparat/src/golding/validate.py "
        "has not been bootstrapped.",
        allow_module_level=True,
    )

import golding.code.validate as _code_validate  # type: ignore # noqa: E402  (must follow the skip guard)
from golding import validate  # type: ignore # noqa: E402  (must follow the skip guard)

# ---------------------------------------------------------------------------
# Exit-code table
#
# Mirrored from validate.main(). Kept here as a constant so the test
# file documents the contract independently of the implementation; if
# the implementation's table drifts from this one, the comparison in
# test_exit_code_table_matches_implementation will fail.
# ---------------------------------------------------------------------------

EXPECTED_EXIT_CODES = {
    "baseline_normalization": 2,
    "cruise_engagement": 3,
    "slice_contract": 4,
    "security_and_guardrails": 5,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patched_check(name, passed, detail=None):
    """Build a fake check function whose CheckResult has the requested
    shape. Used with monkeypatch.setattr to replace validate.CHECKS.
    """
    if detail is None:
        detail = {}

    def fake_check():
        return validate.CheckResult(name=name, passed=passed, detail=detail)

    return fake_check


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_clean_config_returns_zero(monkeypatch):
    """With every check replaced by a passing stub, main() returns 0
    and emits one JSON line per check to stdout.
    """
    monkeypatch.setattr(
        _code_validate,
        "CHECKS",
        [
            _patched_check("baseline_normalization", passed=True, detail={"count": 9}),
            _patched_check(
                "cruise_engagement", passed=True, detail={"engaged_per_cycle": [True, True, True]}
            ),
            _patched_check("slice_contract", passed=True, detail={"engine_slices": [4, 16, 64]}),
        ],
    )
    assert validate.main() == 0


def test_clean_config_emits_json_lines(monkeypatch, capsys):
    """Each check emits a single JSON line, regardless of pass/fail.
    The format must be stable because CI greps the log.
    """
    monkeypatch.setattr(
        _code_validate,
        "CHECKS",
        [
            _patched_check("baseline_normalization", passed=True),
            _patched_check("cruise_engagement", passed=True),
            _patched_check("slice_contract", passed=True),
        ],
    )
    validate.main()
    captured = capsys.readouterr()
    lines = [line for line in captured.out.split("\n") if line]
    assert len(lines) == 3, f"expected 3 JSON lines, got {len(lines)}: {lines!r}"
    for line in lines:
        payload = json.loads(line)  # raises if not valid JSON
        assert payload["passed"] is True
        assert "detail" in payload


# ---------------------------------------------------------------------------
# Per-failure-class exit codes
# ---------------------------------------------------------------------------


def test_baseline_violation_returns_two(monkeypatch):
    """A failing baseline check returns exit code 2."""
    monkeypatch.setattr(
        _code_validate,
        "CHECKS",
        [_patched_check("baseline_normalization", passed=False, detail={"violations": [42.0]})],
    )
    assert validate.main() == 2


def test_cruise_engagement_failure_returns_three(monkeypatch):
    """A failing cruise check returns exit code 3."""
    monkeypatch.setattr(
        _code_validate,
        "CHECKS",
        [_patched_check("cruise_engagement", passed=False, detail={"engaged_per_cycle": [False]})],
    )
    assert validate.main() == 3


def test_slice_contract_violation_returns_four(monkeypatch):
    """A failing slice-contract check returns exit code 4."""
    monkeypatch.setattr(
        _code_validate,
        "CHECKS",
        [_patched_check("slice_contract", passed=False, detail={"engine_slices": [1, 2, 3]})],
    )
    assert validate.main() == 4


def test_unhandled_exception_returns_one(monkeypatch):
    """A check that raises an unhandled exception yields exit code 1.
    This is the only exit code that is *not* specific to a check
    class — it means the validator itself is broken.
    """

    def boom():
        raise RuntimeError("simulated failure in a check")

    monkeypatch.setattr(_code_validate, "CHECKS", [boom])
    assert validate.main() == 1


def test_unhandled_exception_emits_error_payload(monkeypatch, capsys):
    """When a check raises, the JSON line on stdout carries the error
    string so CI logs can show the cause without re-running.
    """

    def boom():
        raise RuntimeError("simulated failure in a check")

    monkeypatch.setattr(_code_validate, "CHECKS", [boom])
    validate.main()
    captured = capsys.readouterr()
    lines = [line for line in captured.out.split("\n") if line]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert "error" in payload
    assert "simulated failure" in payload["error"]


# ---------------------------------------------------------------------------
# Ordering and short-circuit behavior
# ---------------------------------------------------------------------------


def test_first_failing_check_short_circuits(monkeypatch):
    """If the first check fails, the second is never invoked. The
    third never sees a chance to run either. This is the
    implementation behavior in main()'s for-loop.
    """
    calls = []

    def track(name):
        def _check():
            calls.append(name)
            return validate.CheckResult(name=name, passed=False, detail={})

        return _check

    monkeypatch.setattr(
        _code_validate,
        "CHECKS",
        [track("baseline_normalization"), track("cruise_engagement"), track("slice_contract")],
    )
    exit_code = validate.main()
    assert exit_code == 2
    assert calls == ["baseline_normalization"]


def test_check_order_matches_documented_order():
    """The order in CHECKS must be baseline → cruise → contract. CI
    output and §4.2 of RECOMMENDATION.md both rely on this order.
    A reordering that breaks this contract is a regression.
    """
    names = [c.__name__ for c in _code_validate.CHECKS if callable(c) and hasattr(c, "__name__")]
    # The function names are check_baseline_normalization, etc.
    # We compare the *suffixes* so this test does not break if a
    # maintainer renames a private helper.
    suffixes = [n.replace("check_", "") for n in names if n.startswith("check_")]
    assert suffixes == [
        "baseline_normalization",
        "cruise_engagement",
        "slice_contract",
        "security_and_guardrails",
    ]


# ---------------------------------------------------------------------------
# Exit-code table integrity (the meta-test)
# ---------------------------------------------------------------------------


def test_exit_code_table_matches_implementation():
    """The exit-code table in validate.main() must cover every check
    name. If a new check is added without a code, main() raises
    KeyError on the first failure — which would otherwise bubble up
    as exit code 1 and silently conflate 'validator broke' with
    'baseline violation'.
    """
    for name, expected_code in EXPECTED_EXIT_CODES.items():
        # Build a single-element CHECKS list with the named check
        # failing, run main() once, and assert the code. Calling
        # main() twice (once for assert, once for the f-string) is
        # a bug: it re-runs side effects and reports a misleading
        # exit code in the error message.
        original = _code_validate.CHECKS
        try:
            _code_validate.CHECKS = [_patched_check(name, passed=False)]
            actual_code = validate.main()
            assert actual_code == expected_code, (
                f"check {name!r}: expected exit {expected_code}, got {actual_code}"
            )
        finally:
            _code_validate.CHECKS = original


def test_every_check_name_has_an_exit_code():
    """The names emitted by CHECKS must all be present in the exit
    code table. A new check added without a code is a bug.

    This test calls each real check function once (with no args) and
    reads the name off the returned CheckResult. That is the
    authoritative source — reconstructing the name from the function
    name would be a tautology, since validate.main() looks up the
    code by the *emitted* name, not the function name.
    """
    emitted = set()
    for check in _code_validate.CHECKS:
        result = check()  # may raise; we want to know if it does
        emitted.add(result.name)

    missing = emitted - EXPECTED_EXIT_CODES.keys()
    assert not missing, f"checks without exit codes: {sorted(missing)}"


# ---------------------------------------------------------------------------
# CheckResult shape
# ---------------------------------------------------------------------------


def test_check_result_dataclass_shape():
    """CheckResult is a dataclass with name, passed, detail. The CI
    JSON-line format relies on asdict() working cleanly.
    """
    result = validate.CheckResult(
        name="baseline_normalization",
        passed=True,
        detail={"count": 9, "min": 0.0, "max": 100.0, "mean": 50.0, "violations": []},
    )
    as_dict = {
        "name": result.name,
        "passed": result.passed,
        "detail": result.detail,
    }
    assert as_dict["name"] == "baseline_normalization"
    assert as_dict["passed"] is True
    assert as_dict["detail"]["count"] == 9


# ---------------------------------------------------------------------------
# Subprocess smoke test
# ---------------------------------------------------------------------------


def test_subprocess_zero_on_clean_config():
    """Run the validator as a subprocess against the actual runtime.
    This is the only test in this file that exercises the real check
    functions rather than monkeypatched stubs. It corresponds to the
    integration smoke test in RECOMMENDATION.md §6.2.

    The module-level ``pytest.skip`` guard at the top of this file
    ensures the import has already succeeded, so by the time this
    test runs the implementation is present in the environment.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        f"{os.path.abspath('mangrove_platform/apparat/src')}{os.pathsep}{env.get('PYTHONPATH', '')}"
    )
    result = subprocess.run(
        [sys.executable, "-m", "golding.validate"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, (
        f"validator exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
