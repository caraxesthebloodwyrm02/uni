from mangrove_platform.apparat.api import GridCell
from mangrove_platform.apparat.apparat import highlight_handler
from mangrove_platform.apparat.guardrails import PayloadGuard
from mangrove_platform.apparat.horizontal_texture_processor import HorizontalTextureProcessor


def test_highlight_handler_empty_and_whitespace():
    """Verify highlight_handler leaves empty/whitespace texture_type unmodified."""
    processor = HorizontalTextureProcessor(2, 1)
    processor.ipo.input_data = [
        GridCell(0, 0, 1.0, ""),
        GridCell(1, 0, 1.0, "   "),
    ]
    updated = highlight_handler(processor, {})
    assert updated[0].texture_type == ""
    assert updated[1].texture_type == "   "


def test_highlight_handler_tag_combinations():
    """Verify highlight_handler correct article, vowel, and consonant tag assignments."""
    processor = HorizontalTextureProcessor(4, 1)
    processor.ipo.input_data = [
        GridCell(0, 0, 1.0, "the dog"),
        GridCell(1, 0, 1.0, "an apple"),
        GridCell(2, 0, 1.0, "banana"),
        GridCell(3, 0, 1.0, "elephant"),
    ]
    updated = highlight_handler(processor, {})
    assert updated[0].texture_type == "the dog|highlight=article-consonant"
    assert updated[1].texture_type == "an apple|highlight=article-vowel"
    assert updated[2].texture_type == "banana|highlight=consonant"
    assert updated[3].texture_type == "elephant|highlight=vowel"


def test_highlight_handler_idempotency():
    """Verify highlight_handler strips existing highlight tags before re-tagging."""
    processor = HorizontalTextureProcessor(1, 1)
    processor.ipo.input_data = [
        GridCell(0, 0, 1.0, "the dog|highlight=old-tag"),
    ]
    updated = highlight_handler(processor, {})
    assert updated[0].texture_type == "the dog|highlight=article-consonant"


def test_payload_guard_empty_and_weak_tags(monkeypatch):
    """Verify PayloadGuard triggers BUFFERED status for __EMPTY__, __WEAK__, and empty payload."""
    guard = PayloadGuard()

    res_weak = guard.evaluate("__WEAK__test", 1)
    assert res_weak["status"] == "BUFFERED"
    assert res_weak["safe"] is True

    res_empty = guard.evaluate("__EMPTY__test", 1)
    assert res_empty["status"] == "BUFFERED"
    assert res_empty["safe"] is True

    res_blank = guard.evaluate("", 1)
    assert res_blank["status"] == "BUFFERED"
    assert res_blank["safe"] is True


def test_payload_guard_weak_buffer_disabled(monkeypatch):
    """Verify PayloadGuard evaluates weak payload normally if buffer is disabled via env."""
    monkeypatch.setenv("MANGROVE_WEAK_PAYLOAD_BUFFER", "false")
    guard = PayloadGuard()

    res = guard.evaluate("__WEAK__test", 1)
    assert res["status"] == "OK"
    assert res["safe"] is True
