"""Test parse_captured idempotency and work reuse.

Normative source:
- Session S05b User Directive #1:
  "Fix the root cause of duplicate works. parse_captured must look up the existing
   work for the same raw/source record (by source_record_key or raw sha256) and pass
   existing_work_id, so a re-parse keeps anchors instead of minting a new work.
   Add a test: parse the same capture twice via the real parse_captured path
   (no manual existing_work_id) and assert 1 work, anchors preserved, 0 new works."
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from django.core.management import call_command

from anchor_lib.ids import mint_id
from ingest.models import Capture, Source
from ingest.storage import BlobStorage
from parse.models import Anchor, ParseRun, Work


@pytest.mark.django_db
def test_parse_captured_twice_preserves_work_and_anchors(tmp_path: Path) -> None:
    """Parsing the same capture twice via the real parse_captured management command

    must reuse the existing Work, preserve anchors, and mint 0 new works.
    """
    storage = BlobStorage()

    Source.objects.get_or_create(
        source_id="src_ibbi",
        defaults={
            "name": "IBBI Orders Portal",
            "provenance_tier": "OFFICIAL_PORTAL",
            "default_rights_class": "PUBLIC_DOMAIN",
        },
    )

    # Load a small real fixture PDF
    fixture_pdf_path = Path("../eval/fixtures/ibbi/nclt_born_digital_chd.pdf")
    if not fixture_pdf_path.exists():
        fixture_pdf_path = Path("eval/fixtures/ibbi/nclt_born_digital_chd.pdf")
    pdf_bytes = fixture_pdf_path.read_bytes()

    raw_id, _, _ = storage.store_blob(pdf_bytes, content_type="application/pdf")
    suffix = raw_id.split(":", 1)[1][:16]

    # Create a Capture record with valid Crockford ULID
    cap_id = mint_id("cap")
    cap_key = f"nclt:test-idempotency-{suffix}"
    Capture.objects.create(
        capture_id=cap_id,
        raw_id=raw_id,
        source_id="src_ibbi",
        source_record_key=cap_key,
        url="https://ibbi.gov.in/test.pdf",
        change_kind="NEW",
        fetched_at=datetime.now(UTC),
        rights_class="PUBLIC_DOMAIN",
        provenance_tier="OFFICIAL_PORTAL",
    )

    initial_work_count = Work.objects.count()

    # First run of parse_captured
    call_command("parse_captured", limit=1, section="nclt")

    work_count_after_first = Work.objects.count()
    assert work_count_after_first == initial_work_count + 1, (
        "First run should create exactly 1 new Work"
    )

    first_run = ParseRun.objects.filter(raw_ids__contains=[raw_id]).order_by("-created_at").first()
    assert first_run is not None
    first_work_id = first_run.work_id

    first_anchors = set(
        Anchor.objects.filter(work_id=first_work_id, state="LIVE").values_list(
            "anchor_id", flat=True
        )
    )
    assert len(first_anchors) > 0, "First run should assign anchors"

    # Second run of parse_captured (re-parse of the same capture via real command path)
    call_command("parse_captured", limit=1, section="nclt")

    work_count_after_second = Work.objects.count()
    assert work_count_after_second == work_count_after_first, (
        f"Second run must NOT mint any new works (expected {work_count_after_first}, got {work_count_after_second})"
    )

    second_run = ParseRun.objects.filter(raw_ids__contains=[raw_id]).order_by("-created_at").first()
    assert second_run is not None
    assert second_run.parse_id != first_run.parse_id, "Second run creates a new ParseRun"
    assert second_run.work_id == first_work_id, "Second run must reuse the same work_id"
    assert second_run.supersedes_parse_id == first_run.parse_id, (
        "Second run must supersede the first run"
    )

    second_anchors = set(
        Anchor.objects.filter(work_id=first_work_id, state="LIVE").values_list(
            "anchor_id", flat=True
        )
    )
    assert second_anchors == first_anchors, (
        f"Anchors must be 100% preserved on re-parse. Missing: {first_anchors - second_anchors}, Extra: {second_anchors - first_anchors}"
    )
