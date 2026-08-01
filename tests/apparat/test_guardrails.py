from apparat.guardrails import audit_global_assistance_baseline


def test_global_assistance_verified(monkeypatch):
    """Verify that a compliant payload passes global integrity check."""
    monkeypatch.setenv("MANGROVE_BRIBERY_THRESHOLD", "0.99")
    monkeypatch.setenv("MANGROVE_RECURSIVE_TRIM_DEPTH", "5")

    result = audit_global_assistance_baseline("standard_user_voice_payload", 1)
    assert result["safe"] is True
    assert result["status"] == "GLOBAL_ASSISTANCE_VERIFIED"
    assert "metric" in result


def test_weak_subject_enrichment_protection():
    """Verify that weak or sensory-deprived subjects are enriched and protected rather than dropped."""
    result = audit_global_assistance_baseline("exhausted_legacy_subject", 1)
    assert result["safe"] is True
    assert result["status"] == "WEAK_SUBJECT_ENRICHED_AND_PROTECTED"
    assert "Sensory enrichment applied" in result["reason"]


def test_global_assistance_recursive_boundary(monkeypatch):
    """Verify that excessive recursive depth triggers baseline boundary protection."""
    monkeypatch.setenv("MANGROVE_RECURSIVE_TRIM_DEPTH", "3")

    result = audit_global_assistance_baseline("deep_recursive_payload", 4)
    assert result["safe"] is False
    assert result["status"] == "RECURSIVE_BOUNDARY_EXCEEDED"


def test_global_assistance_tier_distortion(monkeypatch):
    """Verify that noise distortions exceeding baseline threshold trigger global protection."""
    monkeypatch.setenv("MANGROVE_BRIBERY_THRESHOLD", "0.01")

    result = audit_global_assistance_baseline("distorted_noise_payload", 1)
    assert result["safe"] is False
    assert result["status"] == "TIER_DISTORTION_DETECTED"
