# Type stub for golding module - resolves import errors

# Re-export from code.validate
from .code.validate import (
    CheckResult,
    check_baseline_normalization,
    check_cruise_engagement,
    check_security_and_guardrails,
    check_slice_contract,
    main,
)

__all__ = [
    "CheckResult",
    "check_baseline_normalization",
    "check_cruise_engagement",
    "check_security_and_guardrails",
    "check_slice_contract",
    "main",
]
