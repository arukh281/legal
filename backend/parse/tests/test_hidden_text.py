"""Test suite for adversarial hidden text detection (Session S05a).

Normative reference:
- docs/03_P1_ingestion_parsing.md §5.2 (hidden text inspection)
- Requirement 6: Untrusted documents are data. Hidden text is flagged and excluded from claimable anchors.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest

from parse.hidden_text import inspect_page_for_hidden_text
from parse.pipeline import ParsingPipeline


@pytest.mark.django_db
class TestHiddenTextInspection:
    """Verifies that white text, tiny fonts, and off-canvas text are flagged and excluded."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.pipeline = ParsingPipeline()
        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent
        self.fixture_path = (
            self.repo_root / "eval" / "fixtures" / "synthetic" / "hidden_text_adversarial.pdf"
        )

    def test_synthetic_adversarial_pdf_flags_all_three_categories(self) -> None:
        doc = pymupdf.open(self.fixture_path)  # type: ignore[no-untyped-call]
        page = doc[0]
        flags, hidden_regions, clean_blocks = inspect_page_for_hidden_text(page, page_number=1)

        assert "WHITE_TEXT" in flags
        assert "TINY_FONT" in flags
        assert "OFF_PAGE" in flags
        assert len(hidden_regions) >= 3

        # Verify that adversarial text was stripped from clean_blocks
        all_clean_text = " ".join(
            span.get("text", "")
            for block in clean_blocks
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        )
        assert "IGNORE PREVIOUS INSTRUCTIONS" not in all_clean_text
        assert "prompt injection watermark" not in all_clean_text
        assert "adversarial text placed far off canvas" not in all_clean_text

    def test_pipeline_quarantines_or_flags_hidden_text_document(self) -> None:
        raw_bytes = self.fixture_path.read_bytes()
        res = self.pipeline.run(raw_bytes, source_metadata={"mime": "application/pdf"})

        assert res.quality.gate in ["FLAGGED", "QUARANTINED"]
        assert len(res.quality.hidden_text_flags) >= 3

        # Ensure no anchor contains the adversarial injection
        for node in res.nodes:
            assert "IGNORE PREVIOUS INSTRUCTIONS" not in node.text
            assert "secret tiny" not in node.text
            assert "far off canvas" not in node.text
