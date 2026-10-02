"""Test suite for golden document outputs (Session S05a).

Normative reference:
- Directive #6: Hand-checked by reading the PDFs, not saved from parser self-output.
- Verifies headers, paragraph counts, and 5 exact anchors per fixture.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
        self._run_golden("nclt_born_digital_chd")

    def test_golden_word_export_nclat(self) -> None:
        self._run_golden("nclat_word_export")

    def test_golden_nclat_delhi(self) -> None:
        self._run_golden("nclat_born_digital_del")

    def test_golden_nclt_scanned_ahm(self) -> None:
        """Scanned NCLT Ahmedabad order (nclt_scanned_ahm.pdf) with recorded OCR."""
        import hashlib

        fixture = GOLDEN_FIXTURES["nclt_scanned_ahm"]
        pdf_path = self.repo_root / fixture["file"]
        assert pdf_path.exists()
        raw_bytes = pdf_path.read_bytes()
        sha = hashlib.sha256(raw_bytes).hexdigest()
        raw_id = f"sha256:{sha}"

        res = self.pipeline.run(
            raw_bytes, raw_id=raw_id, source_metadata={"mime": "application/pdf"}
        )
        self._verify_golden(fixture, res)

    def test_golden_nclt_scanned_ahm_2(self) -> None:
        """Second scanned NCLT Ahmedabad order (sample_order_1.pdf) with recorded OCR."""
        import hashlib

        fixture = GOLDEN_FIXTURES["nclt_scanned_ahm_2"]
        pdf_path = self.repo_root / fixture["file"]
        assert pdf_path.exists()
        raw_bytes = pdf_path.read_bytes()
        sha = hashlib.sha256(raw_bytes).hexdigest()
        raw_id = f"sha256:{sha}"

        res = self.pipeline.run(
            raw_bytes, raw_id=raw_id, source_metadata={"mime": "application/pdf"}
        )
        self._verify_golden(fixture, res)

    def test_golden_nclt_born_digital_mum(self) -> None:
        """Born-digital NCLT Mumbai order (sample_order_2.pdf)."""
        self._run_golden("nclt_born_digital_mum")

    def _run_golden(self, fixture_key: str) -> None:
        """Shared helper for born-digital golden fixture tests."""
        fixture = GOLDEN_FIXTURES[fixture_key]
        pdf_path = self.repo_root / fixture["file"]
        assert pdf_path.exists(), f"Missing fixture file: {pdf_path}"

        raw_bytes = pdf_path.read_bytes()
        res = self.pipeline.run(raw_bytes, source_metadata={"mime": "application/pdf"})
        self._verify_golden(fixture, res)

    def _verify_golden(self, fixture: dict, res: Any) -> None:  # type: ignore[type-arg]
        """Shared assertions for all golden fixtures."""
        expected_h = fixture["header"]
        assert res.header.court_id == expected_h["court_id"]
        assert expected_h["case_number_contains"] in res.header.case_number
        assert res.header.decision_date is not None
        assert res.header.decision_date.isoformat() == expected_h["decision_date"]
        assert expected_h["applicant"].lower() in str(res.header.parties).lower()
        assert expected_h["respondent"].lower() in str(res.header.parties).lower()

        # Paragraph count
        paras = [n for n in res.nodes if n.node_type == "PARA"]
        assert fixture["min_paras"] <= len(paras) <= fixture["max_paras"]

        # Exact anchors with text snippets
        # For multi-section docs with duplicate fragments, collect all
        nodes_by_frag: dict[str, list[Any]] = {}
        for n in res.nodes:
            nodes_by_frag.setdefault(n.fragment, []).append(n)

        for frag, expected_snippet in fixture["anchors"].items():
            assert frag in nodes_by_frag, f"Expected fragment {frag} not found in nodes"
            # At least one node with this fragment must contain the snippet
            found = any(expected_snippet.lower() in n.text.lower() for n in nodes_by_frag[frag])
            assert found, (
                f"Anchor {frag} snippet mismatch: expected '{expected_snippet}' "
                f"not found in any {frag} node"
            )
