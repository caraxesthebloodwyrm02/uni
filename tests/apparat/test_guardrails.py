from mangrove_platform.apparat.guardrails import audit_payload


def test_payload_within_bounds(monkeypatch):
    """A normal payload within configured bounds returns OK."""
    monkeypatch.setenv("MANGROVE_NOISE_THRESHOLD", "0.99")
    monkeypatch.setenv("MANGROVE_MAX_DEPTH", "5")

    result = audit_payload("standard_user_voice_payload", 1)
    assert result["safe"] is True
    assert result["status"] == "OK"
    assert "metric" in result


def test_weak_payload_buffer():
    """A payload marked __WEAK__ or empty triggers the buffer path."""
    result = audit_payload("__WEAK__subject", 1)
    assert result["safe"] is True
    assert result["status"] == "BUFFERED"
    assert "Buffer applied" in result["reason"]


def test_payload_depth_limit(monkeypatch):
    """Exceeding max_depth returns DEPTH_LIMIT."""
    monkeypatch.setenv("MANGROVE_MAX_DEPTH", "3")

    result = audit_payload("deep_recursive_payload", 4)
    assert result["safe"] is False
    assert result["status"] == "DEPTH_LIMIT"


def test_payload_noise_over(monkeypatch):
    """A payload whose sine compression exceeds threshold returns NOISE_OVER."""
    monkeypatch.setenv("MANGROVE_NOISE_THRESHOLD", "0.01")

    result = audit_payload("distorted_noise_payload", 1)
    assert result["safe"] is False
    assert result["status"] == "NOISE_OVER"
