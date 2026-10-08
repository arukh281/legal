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


@pytest.mark.django_db
def test_changed_capture_reuses_work_and_tombstones_deleted_anchors() -> None:
    """When a capture is CHANGED (different raw_id, same source_record_key),

    parse_captured must look up the existing work by source_record_key,
    align anchors to the existing work, preserve unchanged anchors, and
    record tombstones where text was removed.
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

    fixture_dir = Path("../eval/fixtures/ibbi")
    if not fixture_dir.exists():
        fixture_dir = Path("eval/fixtures/ibbi")

    orig_pdf_path = fixture_dir / "sample_order_1.pdf"
    changed_pdf_path = fixture_dir / "sample_order_changed.pdf"

    orig_bytes = orig_pdf_path.read_bytes()
    changed_bytes = changed_pdf_path.read_bytes()

    raw_id_1, _, _ = storage.store_blob(orig_bytes, content_type="application/pdf")
    raw_id_2, _, _ = storage.store_blob(changed_bytes, content_type="application/pdf")
    assert raw_id_1 != raw_id_2

    key = f"nclt:test-amended-{mint_id('cap')}"

    # First capture: original order (NEW)
    cap1 = Capture.objects.create(
        capture_id=mint_id("cap"),
        raw_id=raw_id_1,
        source_id="src_ibbi",
        source_record_key=key,
        url="https://ibbi.gov.in/order1.pdf",
        change_kind="NEW",
        fetched_at=datetime.now(UTC),
        rights_class="PUBLIC_DOMAIN",
        provenance_tier="OFFICIAL_PORTAL",
    )

    initial_work_count = Work.objects.count()

    # Parse original capture
    call_command("parse_captured", capture_id=cap1.capture_id)

    work_count_after_first = Work.objects.count()
    assert work_count_after_first == initial_work_count + 1, "First run creates 1 new Work"

    run1 = ParseRun.objects.filter(raw_ids__contains=[raw_id_1]).order_by("-created_at").first()
    assert run1 is not None
    work_id = run1.work_id

    live_anchors_run1 = set(
        Anchor.objects.filter(work_id=work_id, state="LIVE").values_list("fragment", flat=True)
    )
    assert "p10" in live_anchors_run1
    assert "ord" in live_anchors_run1

    # Second capture: amended order (CHANGED, new raw_id, prior_raw_id pointing to raw_id_1)
    cap2 = Capture.objects.create(
        capture_id=mint_id("cap"),
        raw_id=raw_id_2,
        source_id="src_ibbi",
        source_record_key=key,
        url="https://ibbi.gov.in/order1_amended.pdf",
        change_kind="CHANGED",
        prior_raw_id=raw_id_1,
        fetched_at=datetime.now(UTC),
        rights_class="PUBLIC_DOMAIN",
        provenance_tier="OFFICIAL_PORTAL",
    )

    # Parse changed capture via real command path
    call_command("parse_captured", capture_id=cap2.capture_id)

    work_count_after_second = Work.objects.count()
    # 1. Assert exactly 1 work (work_id reused, 0 new works minted)
    assert work_count_after_second == work_count_after_first, (
        f"Second run must NOT mint a new work (expected {work_count_after_first}, got {work_count_after_second})"
    )

    run2 = ParseRun.objects.filter(raw_ids__contains=[raw_id_2]).order_by("-created_at").first()
    assert run2 is not None
    assert run2.work_id == work_id, "Second run must reuse the same work_id"
    assert run2.supersedes_parse_id == run1.parse_id, "Second run must supersede the first run"

    # 2. Assert anchors preserved or aliased
    live_anchors_run2 = set(
        Anchor.objects.filter(work_id=work_id, state="LIVE").values_list("fragment", flat=True)
    )
    for frag in ["hdr", "u1", "p1", "p2", "p8"]:
        assert frag in live_anchors_run2, f"Surviving anchor #{frag} must remain LIVE"

    # 3. Assert tombstones where text was removed
    tombstoned_run2 = set(
        Anchor.objects.filter(work_id=work_id, state="TOMBSTONED").values_list(
            "fragment", flat=True
        )
    )
    assert len(tombstoned_run2) > 0, "Deleted text must produce tombstones"
    assert "p10" in tombstoned_run2, "Anchor #p10 must be TOMBSTONED where text was removed"
    assert "ord" in tombstoned_run2, "Anchor #ord must be TOMBSTONED where text was removed"
