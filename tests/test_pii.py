"""Tests for PII detection patterns."""

from prompteval.security.pii import scan_for_pii


def _find(text, pii_type):
    """Helper: return findings matching a PII type."""
    return [f for f in scan_for_pii(text) if pii_type in f.description]


# --- US / general patterns ---

def test_ssn_detected():
    results = _find("My SSN is 123-45-6789", "ssn")
    assert len(results) == 1
    assert results[0].severity == "high"


def test_email_detected():
    results = _find("Contact me at user@example.com", "email")
    assert len(results) == 1
    assert results[0].severity == "medium"


def test_credit_card_detected():
    results = _find("Card: 4111 1111 1111 1111", "credit_card")
    assert len(results) == 1
    assert results[0].severity == "high"


def test_us_phone_detected():
    results = _find("Call (555) 123-4567", "phone_us")
    assert len(results) == 1


def test_international_phone_detected():
    results = _find("Call +447911123456", "phone_intl")
    assert len(results) >= 1


def test_international_phone_with_separator():
    results = _find("Call +44-7911123456", "phone_intl")
    assert len(results) >= 1


def test_ip_address_detected():
    results = _find("Server at 192.168.1.1", "ip_address")
    assert len(results) == 1
    assert results[0].severity == "low"


# --- European patterns ---

def test_iban_german():
    results = _find("Account: DE89 3704 0044 0532 0130 00", "iban")
    assert len(results) == 1
    assert results[0].severity == "high"


def test_iban_dutch():
    results = _find("Pay to NL91ABNA0417164300", "iban")
    assert len(results) == 1


def test_iban_british():
    results = _find("IBAN: GB29 NWBK 6016 1331 9268 19", "iban")
    assert len(results) == 1


def test_iban_french():
    results = _find("FR76 3000 6000 0112 3456 7890 189", "iban")
    assert len(results) == 1


def test_eu_phone_french():
    results = _find("Appelez +33 612345678", "phone_eu")
    assert len(results) >= 1


def test_eu_phone_german():
    results = _find("Anrufen +49 15112345678", "phone_eu")
    assert len(results) >= 1


def test_eu_phone_uk():
    results = _find("Ring +44 7911123456", "phone_eu")
    assert len(results) >= 1


def test_eu_phone_italian():
    results = _find("Chiama +39 3312345678", "phone_eu")
    assert len(results) >= 1


# --- Negative cases ---

def test_no_pii_in_clean_text():
    results = scan_for_pii("The weather is nice today.")
    assert len(results) == 0


def test_provider_and_model_propagated():
    results = scan_for_pii("SSN: 123-45-6789", provider="anthropic", model="claude")
    assert results[0].provider == "anthropic"
    assert results[0].model == "claude"


def test_evidence_is_redacted():
    results = scan_for_pii("SSN: 123-45-6789")
    assert "***" in results[0].evidence
