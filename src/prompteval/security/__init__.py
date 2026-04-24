"""Security audit modules."""

from prompteval.security.pii import scan_for_pii
from prompteval.security.injection import run_injection_check
from prompteval.security.jailbreak import run_jailbreak_check

SECURITY_CHECKS = {
    "injection": run_injection_check,
    "pii_detection": scan_for_pii,
    "jailbreak": run_jailbreak_check,
}

__all__ = ["SECURITY_CHECKS", "scan_for_pii", "run_injection_check", "run_jailbreak_check"]
