"""Test suite for golden document outputs (Session S05a).

Normative reference:
- Directive #6: Hand-checked by reading the PDFs, not saved from parser self-output.
- Verifies headers, paragraph counts, and 5 exact anchors per fixture.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from parse.pipeline import ParsingPipeline
from parse.tests.golden_data import GOLDEN_FIXTURES


@pytest.mark.django_db
class TestGoldenOutputs:
    """Verifies that parser accurately extracts headers and assigns anchors on golden fixtures."""

    @pytest.fixture(autouse=True)
    def setup_pipeline(self) -> None:
        self.pipeline = ParsingPipeline()
        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent

    def test_golden_born_digital_nclt_chandigarh(self) -> None:
        fixture = GOLDEN_FIXTURES["nclt_born_digital_chd"]
        pdf_path = self.repo_root / fixture["file"]
        assert pdf_path.exists(), f"Missing fixture file: {pdf_path}"

        raw_bytes = pdf_path.read_bytes()
        res = self.pipeline.run(raw_bytes, source_metadata={"mime": "application/pdf"})

        # 1. Header Verification
        expected_h = fixture["header"]
        assert res.header.court_id == expected_h["court_id"]
        assert expected_h["case_number_contains"] in res.header.case_number
        assert res.header.decision_date is not None
        assert res.header.decision_date.isoformat() == expected_h["decision_date"]
        assert expected_h["applicant"].lower() in str(res.header.parties).lower()
        assert expected_h["respondent"].lower() in str(res.header.parties).lower()

        # 2. Paragraph Count Verification
        paras = [n for n in res.nodes if n.node_type == "PARA"]
        assert fixture["min_paras"] <= len(paras) <= fixture["max_paras"]

        # 3. Exact 5 Anchors Verification
        nodes_by_frag = {n.fragment: n for n in res.nodes}
        for frag, expected_snippet in fixture["anchors"].items():
            assert frag in nodes_by_frag, f"Expected fragment {frag} not found in nodes"
            node = nodes_by_frag[frag]
            assert expected_snippet.lower() in node.text.lower(), (
                f"Anchor {frag} snippet mismatch: expected '{expected_snippet}', got '{node.text[:100]}'"
            )

    def test_golden_word_export_nclat(self) -> None:
        fixture = GOLDEN_FIXTURES["nclat_word_export"]
        pdf_path = self.repo_root / fixture["file"]
        assert pdf_path.exists(), f"Missing fixture file: {pdf_path}"

        raw_bytes = pdf_path.read_bytes()
        res = self.pipeline.run(raw_bytes, source_metadata={"mime": "application/pdf"})

        # Header
        expected_h = fixture["header"]
        assert res.header.court_id == expected_h["court_id"]
        assert expected_h["case_number_contains"] in res.header.case_number
        assert res.header.decision_date is not None
        assert res.header.decision_date.isoformat() == expected_h["decision_date"]

        # Paragraph count & exact anchors
        nodes_by_frag = {n.fragment: n for n in res.nodes}
        for frag, expected_snippet in fixture["anchors"].items():
            assert frag in nodes_by_frag, f"Expected fragment {frag} not found in nodes"
            node = nodes_by_frag[frag]
            assert expected_snippet.lower() in node.text.lower()

    def test_golden_nclat_delhi(self) -> None:
        fixture = GOLDEN_FIXTURES["nclat_born_digital_del"]
        pdf_path = self.repo_root / fixture["file"]
        assert pdf_path.exists(), f"Missing fixture file: {pdf_path}"

        raw_bytes = pdf_path.read_bytes()
        res = self.pipeline.run(raw_bytes, source_metadata={"mime": "application/pdf"})

        expected_h = fixture["header"]
        assert res.header.court_id == expected_h["court_id"]
        assert expected_h["case_number_contains"] in res.header.case_number
        assert res.header.decision_date is not None
        assert res.header.decision_date.isoformat() == expected_h["decision_date"]

        nodes_by_frag = {n.fragment: n for n in res.nodes}
        for frag, expected_snippet in fixture["anchors"].items():
            assert frag in nodes_by_frag, f"Expected fragment {frag} not found in nodes"
            node = nodes_by_frag[frag]
            assert expected_snippet.lower() in node.text.lower()
