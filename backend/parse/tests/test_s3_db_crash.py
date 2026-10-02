"""Test suite for S3 upload and DB atomic transaction separation (Session S05a).

Normative reference:
- User Directive #5: S3 and the DB aren't one transaction. Upload the ParsedDocument
  (content-addressed) first, then commit the DB rows and the event. An orphaned S3
  object is harmless; a DB row pointing to a missing object is not. Test the crash
  between the two steps.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from ops.models import EventOutbox
from parse.consumer import persist_pipeline_result
from parse.models import Anchor, ParseRun
from parse.pipeline import ParsingPipeline
from parse.storage import ParsedDocStorage


@pytest.mark.django_db
class TestS3DatabaseCrashSeparation:
    """Verifies crash resilience between S3 artifact upload and database commit."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.pipeline = ParsingPipeline()
        self.doc_storage = ParsedDocStorage()
        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent
        self.pdf_path = self.repo_root / "eval" / "fixtures" / "ibbi" / "nclt_born_digital_chd.pdf"

    def test_crash_after_s3_upload_leaves_orphaned_s3_but_clean_db(self) -> None:
        raw_bytes = self.pdf_path.read_bytes()

        # Step 1: Execute pipeline run (which uploads ParsedDocument to S3 first)
        result = self.pipeline.run(raw_bytes, source_metadata={"mime": "application/pdf"})
        assert result.parsed_doc_uri.startswith("s3://")

        # Verify S3 object exists immediately after pipeline run
        doc_json = self.doc_storage.fetch_parsed_document(result.parsed_doc_uri)
        assert doc_json is not None
        assert doc_json["ids"]["work_id"] == result.work_id

        # Step 2: Simulate crash during DB persistence (e.g. database error inside atomic block)
        with patch(
            "parse.consumer.Work.objects.get_or_create",
            side_effect=RuntimeError("Simulated DB Crash"),
        ):
            with pytest.raises(RuntimeError, match="Simulated DB Crash"):
                persist_pipeline_result(
                    result,
                    source_id="src_ibbi",
                    raw_id="raw_crash_test",
                    url="https://ibbi.gov.in/orders/crash_test",
                )

        # Step 3: Verify DB has NO rows committed for this parse_id
        assert not ParseRun.objects.filter(parse_id=result.parse_id).exists()
        assert not Anchor.objects.filter(work_id=result.work_id).exists()
        assert not EventOutbox.objects.filter(
            subject=f"{result.work_id}/{result.expression_key}"
        ).exists()

        # S3 object is still safely present (orphaned, content-addressed, harmless)
        doc_json_after = self.doc_storage.fetch_parsed_document(result.parsed_doc_uri)
        assert doc_json_after is not None

        # Step 4: Re-try persistence without simulated crash -> commits cleanly
        persist_pipeline_result(
            result,
            source_id="src_ibbi",
            raw_id="raw_crash_test",
            url="https://ibbi.gov.in/orders/crash_test",
        )
        assert ParseRun.objects.filter(parse_id=result.parse_id).exists()
        assert Anchor.objects.filter(work_id=result.work_id).exists()
