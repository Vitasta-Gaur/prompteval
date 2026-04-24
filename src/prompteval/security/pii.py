"""PII leakage detection via regex patterns."""

import re
from dataclasses import dataclass


@dataclass
class SecurityFinding:
    check_type: str   # "pii", "injection", "jailbreak"
    severity: str     # "low", "medium", "high", "critical"
    description: str
    evidence: str
    provider: str = ""
    model: str = ""


# (pattern, severity, description) — compiled at module load for performance
_PII_PATTERN_DEFS: dict[str, tuple[str, str, str]] = {
    "ssn": (r"\b\d{3}-\d{2}-\d{4}\b", "high", "Social Security Number detected"),
    "email": (r"\b[\w.-]+@[\w.-]+\.\w{2,}\b", "medium", "Email address detected"),
    "credit_card": (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "high", "Credit card number detected"),
    "phone_us": (r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "medium", "US phone number detected"),
    "phone_intl": (r"(?<!\w)\+\d{1,3}[-.\s]?\d{4,14}\b", "medium", "International phone number detected"),
    "phone_eu": (
        r"(?<!\w)\+?(?:30|31|32|33|34|35[0-9]|36|37[0-9]|38[0-9]|39|40|41|42[0-9]|43|44|45|46|47|48|49)"
        r"[-.\s]?\d{4,12}\b",
        "medium",
        "European phone number detected",
    ),
    "iban": (
        r"\b[A-Z]{2}\d{2}[-\s]?[A-Z0-9]{4}[-\s]?(?:[A-Z0-9]{4}[-\s]?){2,7}[A-Z0-9]{1,4}\b",
        "high",
        "IBAN account number detected",
    ),
    "ip_address": (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "low", "IP address detected"),
}

# Pre-compiled patterns: name -> (compiled_regex, severity, description)
PII_PATTERNS: dict[str, tuple[re.Pattern, str, str]] = {
    name: (re.compile(pattern), severity, desc)
    for name, (pattern, severity, desc) in _PII_PATTERN_DEFS.items()
}


def scan_for_pii(text: str, provider: str = "", model: str = "") -> list[SecurityFinding]:
    """Scan text for PII patterns. Returns list of findings."""
    findings = []
    for name, (compiled_re, severity, description) in PII_PATTERNS.items():
        matches = compiled_re.findall(text)
        for match in matches:
            # Redact the middle of the match for the evidence
            redacted = match[:3] + "***" + match[-3:] if len(match) > 6 else "***"
            findings.append(SecurityFinding(
                check_type="pii",
                severity=severity,
                description=f"{description} ({name})",
                evidence=f"Found: {redacted}",
                provider=provider,
                model=model,
            ))
    return findings
