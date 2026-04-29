from app.api.base import extract_keywords
from app.utils import humanize_seconds, parse_quotes


def test_parse_quotes_blank_line_separates():
    text = """The journey of a thousand miles
begins with a single step.

# this is a comment

Stay hungry, stay foolish.
"""
    quotes = parse_quotes(text)
    assert len(quotes) == 2
    assert quotes[0].startswith("The journey")
    assert quotes[1] == "Stay hungry, stay foolish."


def test_parse_quotes_strips_blanks():
    assert parse_quotes("") == []
    assert parse_quotes("\n\n\n") == []


def test_extract_keywords_skips_stopwords():
    kws = extract_keywords("The journey of a thousand miles begins with a single step")
    # 'the', 'of', 'a', 'with' are stopwords; 'journey' should appear first
    assert kws.split()[0] == "journey"
    assert "the" not in kws.split()


def test_extract_keywords_fallback():
    assert extract_keywords("") == "motivation nature"
    assert extract_keywords("a the of") == "motivation nature"


def test_humanize_seconds():
    assert humanize_seconds(0) == "00:00"
    assert humanize_seconds(65) == "01:05"
    assert humanize_seconds(3725) == "1:02:05"
