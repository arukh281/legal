"""Test suite for doc.parsed.v1 outbox event contract (Session S05a).

Normative references:
- docs/01_master_architecture.md §6.2 (CloudEvents envelope), §6.3 (doc.parsed.v1 payload)
- User Directive #1: Topic is plc.doc.parsed.v1, lane goes in the lane column.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ops.models import EventOutbox
from parse.consumer import persist_pipeline_result
from parse.pipeline import ParsingPipeline


@pytest.mark.django_db
class TestDocParsedEventContract:
    """Verifies that doc.parsed.v1 events conform strictly to 01 §6.3 and Directive #1."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.pipeline = ParsingPipeline()
        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent
        self.pdf_path = self.repo_root / "eval" / "fixtures" / "ibbi" / "nclt_born_digital_chd.pdf"

    def test_doc_parsed_v1_envelope_and_payload_structure(self) -> None:
        raw_bytes = self.pdf_path.read_bytes()
        res = self.pipeline.run(raw_bytes, source_metadata={"mime": "application/pdf"})

        persist_pipeline_result(
            res,
            source_id="src_ibbi",
            raw_id="raw_event_test",
            url="https://ibbi.gov.in/orders/test",
            lane="rt",
        )

        event = EventOutbox.objects.filter(type="doc.parsed.v1").order_by("-created_at").first()
        assert event is not None, "doc.parsed.v1 event was not published to outbox"

        # Directive #1: Topic is plc.doc.parsed.v1, lane is in lane column
        assert event.topic == "plc.doc.parsed.v1"
        assert event.lane == "rt"
        assert event.dataclass == "PUBLIC"
        assert event.dataschema == "schemareg://plc/doc.parsed.v1/1.0"
        assert event.subject == f"{res.work_id}/{res.expression_key}"

        # 01 §6.3 payload fields
        data = event.data
        required_fields = [
            "parse_id",
            "raw_ids",
            "manifestation_id",
            "work_id",
            "work_id_status",
            "case_id",
            "case_ids",
            "expression_key",
            "doc_type",
            "metadata",
            "parsed_doc_uri",
            "citations",
            "statute_mentions_count",
            "quality",
            "supersedes_parse_id",
            "anchor_changes",
            "rights_class",
            "provenance_tier",
            "pipeline_version",
        ]
        for field in required_fields:
            assert field in data, f"Missing 01 §6.3 payload field: {field}"

        # Quality object
        quality = data["quality"]
        for q_field in [
            "ocr_conf",
            "lang",
            "structure_conf",
            "needs_review",
            "gate",
            "hidden_text_flags",
        ]:
            assert q_field in quality, f"Missing quality field: {q_field}"
