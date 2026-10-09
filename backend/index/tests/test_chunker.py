"""Tests for StructureChunker, Invariants I1–I6, long paragraph splitting, and headers.

Normative sources:
- docs/04_P2_enrichment_indexing.md §5.2A, §5.3, §5.4
- Directives #3 & #4 approved by aru:
  - Long paragraphs split into JUDG_LONG_PARA_PART with body.part = {k, n, char_start, char_end}
  - Invariant I5 verifies parts joined in order equal parent text
  - role_source = "FALLBACK", rhetorical_role = None
"""

from __future__ import annotations

import pytest

from index.chunker import InvariantViolationError, StructureChunker
from index.headers import build_context_header


def test_structure_chunker_basic_narrative() -> None:
    """Test chunker produces JUDG_PARA_GROUP and respects token bounds."""
    doc = {
        "nodes": [
            {"anchor_id": "wrk_1/en#p1", "type": "paragraph", "text": "Paragraph 1 text."},
            {"anchor_id": "wrk_1/en#p2", "type": "paragraph", "text": "Paragraph 2 text."},
            {"anchor_id": "wrk_1/en#ord", "type": "paragraph", "text": "Ordered that appeal is dismissed."},
        ],
        "doc_type": "JUDGMENT",
        "work_id": "wrk_1",
        "expression_key": "en",
    }

    chunker = StructureChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 2
    # First chunk is narrative paragraph group
    assert chunks[0].chunk_kind == "JUDG_PARA_GROUP"
    assert chunks[0].anchor_ids == ["wrk_1/en#p1", "wrk_1/en#p2"]
    assert chunks[0].role_source == "FALLBACK"
    assert chunks[0].rhetorical_role is None

    # Second chunk is operative order
    assert chunks[1].chunk_kind == "JUDG_OPERATIVE_ORDER"
    assert chunks[1].anchor_ids == ["wrk_1/en#ord"]
    assert chunks[1].role_source == "FALLBACK"


def test_long_paragraph_splitting_directive_3() -> None:
    """Directive #3: Paragraphs > 900 tokens split into JUDG_LONG_PARA_PART under parent anchor."""
    # Generate a very long paragraph (~1200 words / tokens)
    sentence = "The applicant submits that the debt fell due on 15th January 2020. "
    long_text = sentence * 120

    doc = {
        "nodes": [
            {"anchor_id": "wrk_1/en#p45", "type": "paragraph", "text": long_text},
            {"anchor_id": "wrk_1/en#ord", "type": "paragraph", "text": "Application allowed."},
        ],
        "doc_type": "JUDGMENT",
        "work_id": "wrk_1",
        "expression_key": "en",
    }

    chunker = StructureChunker()
    chunks = chunker.chunk_document(doc)

    long_parts = [c for c in chunks if c.chunk_kind == "JUDG_LONG_PARA_PART"]
    assert len(long_parts) > 1

    # Verify parent anchor is preserved on every part
    for part in long_parts:
        assert part.anchor_ids == ["wrk_1/en#p45"]
        part_info = part.body_extra.get("part", {})
        assert "k" in part_info
        assert "n" in part_info
        assert part_info["n"] == len(long_parts)
        assert "char_start" in part_info
        assert "char_end" in part_info

    # Verify part numbering 1..N
    assert [p.body_extra["part"]["k"] for p in long_parts] == list(range(1, len(long_parts) + 1))


def test_short_order_whole() -> None:
    """Orders with total tokens <= 700 are emitted as SHORT_ORDER_WHOLE."""
    doc = {
        "nodes": [
            {"anchor_id": "wrk_1/en#p1", "type": "paragraph", "text": "Short hearing held today."},
            {"anchor_id": "wrk_1/en#ord", "type": "paragraph", "text": "Matter adjourned to 10th May."},
        ],
        "doc_type": "ORDER",
        "work_id": "wrk_1",
        "expression_key": "en",
    }

    chunker = StructureChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 1
    assert chunks[0].chunk_kind == "SHORT_ORDER_WHOLE"
    assert chunks[0].anchor_ids == ["wrk_1/en#p1", "wrk_1/en#ord"]


def test_invariant_i1_violation_raises() -> None:
    """I1: All input non-empty anchors must be covered."""
    chunker = StructureChunker()
    # If chunks list drops an anchor, _validate_invariants raises InvariantViolationError
    with pytest.raises(InvariantViolationError, match="Invariant I1 violated"):
        chunker._validate_invariants(
            chunks=[],
            all_input_anchors=["wrk_1/en#p1"],
        )


def test_context_header_format() -> None:
    """Verify deterministic context header formatting."""
    header = build_context_header(
        court_name="Supreme Court of India",
        bench_strength=3,
        decision_date="2024-02-05",
        title="ABC v. XYZ",
        first_anchor="wrk_1/en#p45",
        last_anchor="wrk_1/en#p47",
        section_heading="Submissions",
        cited_provisions=["s. 7 IBC"],
        cited_cases_norm=["(2021) 9 SCC 657"],
    )

    assert "Supreme Court of India" in header
    assert "3-judge bench" in header
    assert "2024-02-05" in header
    assert "ABC v. XYZ" in header
    assert "¶¶ p45–p47" in header
    assert "Submissions" in header
    assert "cites: s. 7 IBC; (2021) 9 SCC 657" in header
