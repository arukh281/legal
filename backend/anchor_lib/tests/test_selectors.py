"""Tests for QuoteSelector implementation.

Normative sources:
- docs/01_master_architecture.md §5.5 item 7 & §7.1 line 963
- docs/mvp/03_data_model_and_contracts.md §1 item 6 & §3.4 line 283
"""

from __future__ import annotations

import pytest

from anchor_lib.selectors import QuoteSelector


def test_quote_selector_from_text_and_serialization() -> None:
    text = (
        "The Supreme Court observed that insolvency resolution is a collective process "
        "and individual creditors cannot derail the corporate debtor's turnaround."
    )
    start = text.index("insolvency resolution is a collective process")
    end = start + len("insolvency resolution is a collective process")

    selector = QuoteSelector.from_text(text, start, end, max_context=32)
    assert selector.exact == "insolvency resolution is a collective process"
    assert selector.prefix == "The Supreme Court observed that "
    assert selector.suffix == " and individual creditors cannot"

    # Serialization roundtrip
    d = selector.to_dict()
    assert d == {
        "exact": "insolvency resolution is a collective process",
        "prefix": "The Supreme Court observed that ",
        "suffix": " and individual creditors cannot",
    }
    rebuilt = QuoteSelector.from_dict(d)
    assert rebuilt == selector


def test_quote_selector_disambiguation_with_repeated_phrases() -> None:
    """Ensure QuoteSelector finds the correct occurrence when exact text appears multiple times."""
    text = (
        "In section 7, the committee considered the report. Later in section 9, the committee "
        "considered the report again after receiving the forensic audit."
    )
    target_phrase = "the committee considered the report"

    # Target the SECOND occurrence
    second_start = text.index(target_phrase, text.index(target_phrase) + 1)
    second_end = second_start + len(target_phrase)

    selector = QuoteSelector.from_text(text, second_start, second_end, max_context=20)
    found_range = selector.find_in(text)
    assert found_range is not None
    assert found_range == (second_start, second_end)

    # Shifted/reformatted text simulation (minor prefix change earlier in doc)
    modified_text = (
        "In s.7, the committee considered the report. Later in section 9, the committee "
        "considered the report again after receiving the audit."
    )
    shifted_range = selector.find_in(modified_text)
    assert shifted_range is not None
    assert modified_text[shifted_range[0] : shifted_range[1]] == target_phrase


def test_quote_selector_not_found() -> None:
    selector = QuoteSelector(
        exact="phrase completely absent from document", prefix="foo", suffix="bar"
    )
    assert selector.find_in("Some text that does not contain that phrase.") is None


def test_quote_selector_invalid_offsets() -> None:
    with pytest.raises(ValueError):
        QuoteSelector.from_text("Short text", 5, 2)
    with pytest.raises(ValueError):
        QuoteSelector.from_text("Short text", -1, 5)
    with pytest.raises(ValueError):
        QuoteSelector.from_text("Short text", 0, 100)
