#!/usr/bin/env python3
"""Apparat Lifecycle handler tests."""

import pytest

from mangrove_platform.apparat.api import GridCell
from mangrove_platform.apparat.horizontal_texture_processor import HorizontalTextureProcessor
from mangrove_platform.apparat.phase_handlers import (
    combine_handler,
    complete_handler,
    compliance_baseline_handler,
    initiate_handler,
    quantize_handler,
    render_handler,
)


class DummyGenerator:
    def generate(self, count: int):
        return [("patternA", "patternB")]


@pytest.fixture
def processor():
    proc = HorizontalTextureProcessor(2, 2)
    proc.generator = DummyGenerator()  # type: ignore[invalid-assignment]
    return proc


def test_initiate_handler(processor):
    cells = initiate_handler(processor, {})
    assert len(cells) == 4
    assert all(c.value == 0.0 and c.texture_type == "empty" for c in cells)
    assert processor.ipo.input_data == cells


def test_quantize_handler(processor):
    # Empty input
    processor.ipo.input_data = []
    assert quantize_handler(processor, {}) == []

    # Non-empty input
    processor.ipo.input_data = [
        GridCell(0, 0, 1.234, "acoustic"),
        GridCell(1, 0, 5.678, "natural"),
    ]
    res = quantize_handler(processor, {})
    assert res[0].value == 1.2
    assert res[1].value == 5.7


def test_combine_handler(processor):
    # Empty input
    processor.ipo.input_data = []
    assert combine_handler(processor, {}) == []

    # Non-empty input
    processor.ipo.input_data = [
        GridCell(0, 0, 1.0, "base"),
        GridCell(1, 0, 2.0, "base"),
    ]
    res = combine_handler(processor, {})
    assert len(res) == 2
    assert res[0].texture_type == "patternA-patternB"


def test_render_handler(processor):
    processor.ipo.input_data = [GridCell(0, 0, 1.0, "acoustic")]
    res = render_handler(processor, {})
    assert res == processor.ipo.input_data

    processor.ipo.processed_data = [GridCell(0, 0, 9.0, "rendered")]
    res = render_handler(processor, {})
    assert res == processor.ipo.processed_data


def test_complete_handler(processor):
    processor.ipo.input_data = [GridCell(0, 0, 1.0, "done")]
    assert complete_handler(processor, {}) == processor.ipo.input_data


def test_compliance_baseline_handler(processor, tmp_path):
    # Test with explicit compliance_root
    processor.ipo.compliance_root = str(tmp_path)
    res = compliance_baseline_handler(processor, {})
    assert res == processor.ipo.input_data

    license_file = tmp_path / "LICENSE"
    notice_file = tmp_path / "NOTICE"
    terms_file = tmp_path / "TERMS_OF_ENGAGEMENT.md"

    assert license_file.exists()
    assert notice_file.exists()
    assert terms_file.exists()
    assert processor.ipo.compliance_artifacts is not None
    assert len(processor.ipo.compliance_artifacts) == 3
