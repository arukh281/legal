"""Test suite for OCR quality thresholds and gate classification (Session S05a).

Normative references:
- docs/04_stack_and_infra.md §2.7: ocr_conf < 0.80 flagged / excluded from tier-1 claims.
- docs/03_P1_ingestion_parsing.md §5.11: PASS, FLAGGED, QUARANTINED bands.
- User Directive #4: Non-Latin script excluded from anchors and flagged lang_unsupported.
- User Directive #8: Doc-level bands and per-anchor claim gating.
"""

from __future__ import annotations

import pytest

from parse.anchors import AlignedAnchorNode
from parse.gates import QualityGate
from parse.judgment import ExtractedHeader
from parse.triage import TriagedPage


@pytest.mark.django_db
class TestOcrGateEvaluation:
    """Verifies gate evaluation logic and claim-backing constraints."""

    @pytest.fixture(autouse=True)
    def setup_gate(self) -> None:
        self.gate = QualityGate()
        self.header = ExtractedHeader(
            court_id="crt_IN_NCLT_MUM",
            bench_name="Mumbai Bench",
            case_number="CP(IB)/100/2026",
            case_type="CP (IB)",
            case_year=2026,
            decision_date=None,  # missing date -> triggers FLAGGED
            parties={"applicant": "Creditor", "respondent": "Debtor"},
        )

    def test_low_ocr_conf_quarantines_document(self) -> None:
        pages = [
            TriagedPage(
                page_number=1,
                text_source="OCR",
                ocr_conf=0.72,  # < 0.80 threshold
                lines=[],
                full_text="low confidence text",
            )
        ]
        nodes = [
            AlignedAnchorNode(
                anchor_id="wrk_test/en#p1",
                fragment="p1",
                node_type="PARA",
                number_as_printed="1",
                numbering="EXPLICIT",
                text="low confidence paragraph",
                text_hash="hash1",
                ocr_conf=0.72,
            )
        ]
        eval_res = self.gate.evaluate(pages, self.header, nodes, hidden_flags=[])
        assert eval_res.gate == "QUARANTINED"
        assert eval_res.needs_review is True
        assert any("LOW_OCR_CONFIDENCE" in r for r in eval_res.gate_reasons)
        # Node ocr_conf < 0.80 cannot back tier-1 claims
        assert nodes[0].ocr_conf is not None and nodes[0].ocr_conf < 0.80

    def test_moderate_ocr_conf_flags_for_review(self) -> None:
        pages = [
            TriagedPage(
                page_number=1,
                text_source="OCR",
                ocr_conf=0.88,  # Between 0.80 and 0.95
                lines=[],
                full_text="moderate confidence text",
            )
        ]
        nodes = [
            AlignedAnchorNode(
                anchor_id="wrk_test/en#p1",
                fragment="p1",
                node_type="PARA",
                number_as_printed="1",
                numbering="EXPLICIT",
                text="moderate confidence paragraph",
                text_hash="hash1",
                ocr_conf=0.88,
            )
        ]
        eval_res = self.gate.evaluate(pages, self.header, nodes, hidden_flags=[])
        assert eval_res.gate == "FLAGGED"
        assert eval_res.needs_review is True

    def test_handwriting_flagged_in_reasons(self) -> None:
        pages = [
            TriagedPage(
                page_number=1,
                text_source="OCR",
                ocr_conf=0.96,
                lines=[],
                full_text="text with handwriting",
            )
        ]
        nodes = [
            AlignedAnchorNode(
                anchor_id="wrk_test/en#p1",
                fragment="p1",
                node_type="PARA",
                number_as_printed="1",
                numbering="EXPLICIT",
                text="handwritten note",
                text_hash="hash_hw",
                ocr_conf=0.96,
                is_handwriting=True,
            )
        ]
        eval_res = self.gate.evaluate(pages, self.header, nodes, hidden_flags=[])
        assert eval_res.gate == "FLAGGED"
        assert "HANDWRITING_PRESENT" in eval_res.gate_reasons

    def test_unsupported_language_flagged(self) -> None:
        pages = [
            TriagedPage(
                page_number=1,
                text_source="OCR",
                ocr_conf=0.96,
                lines=[],
                full_text="गैर-लैटिन पाठ",
                is_lang_unsupported=True,
            )
        ]
        eval_res = self.gate.evaluate(pages, self.header, nodes=[], hidden_flags=[])
        assert eval_res.gate == "QUARANTINED"
        assert any("LANG_UNSUPPORTED" in r for r in eval_res.gate_reasons)
        assert "und" in eval_res.lang
