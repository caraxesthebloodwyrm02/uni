import pytest

from mangrove_platform.apparat.api import GridCell
from mangrove_platform.apparat.horizontal_texture_processor import HorizontalTextureProcessor

# Define a standard 2x2 input grid for all gold tests
# Grid:
# (0,0) value=10.0, type="acoustic"
# (1,0) value=20.0, type="natural"
# (0,1) value=30.0, type="acoustic"
# (1,1) value=40.0, type="natural"
GOLD_INPUT = [
    GridCell(0, 0, 10.0, "acoustic"),
    GridCell(1, 0, 20.0, "natural"),
    GridCell(0, 1, 30.0, "acoustic"),
    GridCell(1, 1, 40.0, "natural"),
]


@pytest.fixture
def processor():
    proc = HorizontalTextureProcessor(2, 2)
    proc.ipo.input_data = GOLD_INPUT[:]
    return proc


def test_normalize_gold(processor):
    """Verify normalization to [0.0, 1.0] range."""
    # Expected: 10->0.0, 20->0.333..., 30->0.666..., 40->1.0
    # Calculation: (val - 10) / (40 - 10)
    result = processor.process_phase("normalize")

    expected = [
        GridCell(0, 0, 0.0, "acoustic"),
        GridCell(1, 0, 10.0 / 30.0, "natural"),
        GridCell(0, 1, 20.0 / 30.0, "acoustic"),
        GridCell(1, 1, 1.0, "natural"),
    ]
    assert result == expected


def test_scale_gold(processor):
    """Verify value multiplication by factor 2.0."""
    result = processor.process_phase("scale:2.0")

    expected = [
        GridCell(0, 0, 20.0, "acoustic"),
        GridCell(1, 0, 40.0, "natural"),
        GridCell(0, 1, 60.0, "acoustic"),
        GridCell(1, 1, 80.0, "natural"),
    ]
    assert result == expected


def test_clamp_gold(processor):
    """Verify clipping of values outside [15.0, 35.0] range."""
    result = processor.process_phase("clamp:15.0,35.0")

    expected = [
        GridCell(0, 0, 15.0, "acoustic"),
        GridCell(1, 0, 20.0, "natural"),
        GridCell(0, 1, 30.0, "acoustic"),
        GridCell(1, 1, 35.0, "natural"),
    ]
    assert result == expected


def test_invert_gold(processor):
    """Verify 1.0 - value transformation.
    Note: This handler expects values typically in [0,1], but the
    math is just 1.0 - val.
    """
    # Set input to normalized values first to make sense of 'invert'
    processor.ipo.input_data = [
        GridCell(0, 0, 0.0, "acoustic"),
        GridCell(1, 0, 0.3, "natural"),
        GridCell(0, 1, 0.6, "acoustic"),
        GridCell(1, 1, 1.0, "natural"),
    ]
    result = processor.process_phase("invert")

    expected = [
        GridCell(0, 0, 1.0, "acoustic"),
        GridCell(1, 0, 0.7, "natural"),
        GridCell(0, 1, 0.4, "acoustic"),
        GridCell(1, 1, 0.0, "natural"),
    ]
    assert result == expected


def test_highlight_gold(processor):
    """Verify texture labels are correctly annotated with tags.
    Input labels: 'acoustic', 'natural'
    - acoustic: vowel ('a'), consonant ('c'), article (no) -> vowel-consonant
    - natural: consonant ('n'), article (no) -> consonant
    """
    # Override input with specific labels to test rules
    processor.ipo.input_data = [
        GridCell(0, 0, 1.0, "the apple"),  # article, vowel
        GridCell(1, 0, 1.0, "banana"),  # consonant
        GridCell(0, 1, 1.0, "an orange"),  # article, vowel
        GridCell(1, 1, 1.0, "sky"),  # consonant
    ]
    result = processor.process_phase("highlight")

    # 'the apple' -> first word 'the' (article), 'apple' (vowel)
    # Wait, the current logic in highlight_handler:
    # first_word = label.split()[0].lower()
    # if first_word in articles: tags.append("article")
    # if first_word and first_word[0] in vowels: tags.append("vowel")

    # 'the apple' -> 'the' is article, 't' is consonant. Tags: [article, consonant]
    # 'banana' -> 'banana' is not article, 'b' is consonant. Tags: [consonant]
    # 'an orange' -> 'an' is article, 'a' is vowel. Tags: [article, vowel]
    # 'sky' -> 'sky' is not article, 's' is consonant. Tags: [consonant]

    expected = [
        GridCell(0, 0, 1.0, "the apple|highlight=article-consonant"),
        GridCell(1, 0, 1.0, "banana|highlight=consonant"),
        GridCell(0, 1, 1.0, "an orange|highlight=article-vowel"),
        GridCell(1, 1, 1.0, "sky|highlight=consonant"),
    ]
    assert result == expected
