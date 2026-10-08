"""Tests for the retire_duplicate_works management command.

Ensures:
- Single transaction retirement of duplicate works into canonical works
- Before and after counts accuracy
- Zero deletions across all tables (Work, ParseRun, Anchor, Manifestation)
- No citations or STUB aliases point to duplicate works
- Full audit recording in plc.identity_merge_ledger and ops.event_outbox
- Idempotency when re-run
"""

from __future__ import annotations

import io
from datetime import UTC, datetime

import pytest
from django.core.management import call_command

from anchor_lib.ids import mint_id
from ingest.models import Capture, RawBlob, Source
from ops.models import EventOutbox
from parse.models import (
    Anchor,
    CitationMention,
    Expression,
    IdentifierAlias,
    IdentityMergeLedger,
    Manifestation,
    ParseRun,
    Work,
)


@pytest.mark.django_db
def test_retire_duplicate_works_command() -> None:
    # Set up source
    Source.objects.get_or_create(
        source_id="src_ibbi",
        defaults={
            "name": "IBBI Orders Portal",
            "provenance_tier": "OFFICIAL_PORTAL",
            "default_rights_class": "PUBLIC_DOMAIN",
        },
    )

    raw_id = "sha256:" + "a" * 64

    RawBlob.objects.create(
        raw_id=raw_id,
        storage_uri=f"s3://test-bucket/{raw_id}",
        byte_size=1024,
        content_type="application/pdf",
        first_seen_at=datetime.now(UTC),
    )

    # Capture record
    Capture.objects.create(
        capture_id=mint_id("cap"),
        raw_id=raw_id,
        source_id="src_ibbi",
        source_record_key="nclt:test-retire-1",
        change_kind="NEW",
        fetched_at=datetime.now(UTC),
        rights_class="PUBLIC_DOMAIN",
        provenance_tier="OFFICIAL_PORTAL",
    )

    # 1. Canonical Work (created later / latest parse run)
    can_work = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
    )
    Expression.objects.create(
        work=can_work,
        expression_key="en",
        lang="en",
        authoritative=True,
    )
    run_latest = ParseRun.objects.create(
        parse_id=mint_id("par"),
        raw_ids=[raw_id],
        work=can_work,
        expression_key="en",
        doc_type="JUDGMENT",
        parsed_doc_uri="s3://fake-latest",
        parsed_doc_sha256="fake-hash-latest",
        quality={},
        gate="PASS",
        anchor_changes={},
        pipeline_version_id="p1.parser@0.1.0|det_v1",
        created_at=datetime(2026, 10, 2, 12, 0, tzinfo=UTC),
    )
    Manifestation.objects.create(
        manifestation_id=mint_id("man"),
        work=can_work,
        expression_key="en",
        raw_ids=[raw_id],
        rights_class="PUBLIC_DOMAIN",
        provenance_tier="OFFICIAL_PORTAL",
    )

    # 2. Duplicate Work (older parse run)
    dup_work = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
    )
    Expression.objects.create(
        work=dup_work,
        expression_key="en",
        lang="en",
        authoritative=True,
    )
    run_older = ParseRun.objects.create(
        parse_id=mint_id("par"),
        raw_ids=[raw_id],
        work=dup_work,
        expression_key="en",
        doc_type="JUDGMENT",
        parsed_doc_uri="s3://fake-older",
        parsed_doc_sha256="fake-hash-older",
        quality={},
        gate="PASS",
        anchor_changes={},
        pipeline_version_id="p1.parser@0.1.0|det_v1",
        created_at=datetime(2026, 10, 2, 8, 0, tzinfo=UTC),
    )
    ParseRun.objects.filter(parse_id=run_older.parse_id).update(
        created_at=datetime(2026, 10, 2, 8, 0, tzinfo=UTC)
    )
    ParseRun.objects.filter(parse_id=run_latest.parse_id).update(
        created_at=datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
    )

    man_dup = Manifestation.objects.create(
        manifestation_id=mint_id("man"),
        work=dup_work,
        expression_key="en",
        raw_ids=[raw_id],
        rights_class="PUBLIC_DOMAIN",
        provenance_tier="OFFICIAL_PORTAL",
    )

    # Add an anchor to both
    Anchor.objects.create(
        anchor_id=f"{can_work.work_id}/en#p1",
        work=can_work,
        expression_key="en",
        fragment="p1",
        node_type="PARA",
        text="Canonical para 1",
        text_hash="hash1",
        lang="en",
        is_authoritative_expression=True,
        state="LIVE",
        first_parse_id=run_latest.parse_id,
        last_parse_id=run_latest.parse_id,
    )
    Anchor.objects.create(
        anchor_id=f"{dup_work.work_id}/en#p1",
        work=dup_work,
        expression_key="en",
        fragment="p1",
        node_type="PARA",
        text="Older para 1",
        text_hash="hash2",
        lang="en",
        is_authoritative_expression=True,
        state="LIVE",
        first_parse_id=run_older.parse_id,
        last_parse_id=run_older.parse_id,
    )

    # Add a citation pointing to dup_work to test re-pointing
    CitationMention.objects.create(
        mention_id=mint_id("cm"),
        parse=run_older,
        anchor_id=f"{dup_work.work_id}/en#p1",
        citing_work=dup_work,
        mention_kind="CASE",
        scheme="SCC",
        raw_text="2020 SCC 100",
        normalized="2020:scc:100",
        pin={"quote_selector": {"prefix": "", "exact": "2020 SCC 100", "suffix": ""}},
        resolution_confidence=0.95,
        resolved_target_id=dup_work.work_id,
        resolution_method="STUB_MINTED",
    )

    # Add an alias on dup_work
    IdentifierAlias.objects.create(
        scheme="SCC",
        value_normalized="2020:scc:100",
        target_id=dup_work.work_id,
        confidence=1.0,
        trust_tier="T4",
        source="citation_mention",
        status="ACTIVE",
        first_seen=datetime.now(UTC),
    )

    out_dry = io.StringIO()
    call_command("retire_duplicate_works", dry_run=True, stdout=out_dry)
    assert "[DRY RUN] Rolled back" in out_dry.getvalue()

    # Verify no state mutated after dry run
    dup_work.refresh_from_db()
    assert dup_work.status == "ACTIVE"
    assert dup_work.merged_into is None

    # Now execute real retirement
    out_real = io.StringIO()
    call_command("retire_duplicate_works", stdout=out_real)
    output = out_real.getvalue()
    assert "Successfully retired 1 duplicate works" in output

    # 1. Assert duplicate work is MERGED into canonical work
    dup_work.refresh_from_db()
    assert dup_work.status == "MERGED"
    assert dup_work.merged_into_id == can_work.work_id

    # 2. Assert canonical work remains ACTIVE
    can_work.refresh_from_db()
    assert can_work.status == "ACTIVE"
    assert can_work.merged_into is None

    # 3. Assert zero deletes: Work, ParseRun, Anchor, Manifestation counts unchanged
    assert Work.objects.count() == 2
    assert ParseRun.objects.count() == 2
    assert Anchor.objects.count() == 2
    assert Manifestation.objects.count() == 2

    # 4. Assert Manifestation re-pointed to canonical work
    man_dup.refresh_from_db()
    assert man_dup.work_id == can_work.work_id

    # 5. Assert CitationMention re-pointed to canonical work
    assert CitationMention.objects.filter(resolved_target_id=dup_work.work_id).count() == 0
    assert CitationMention.objects.filter(resolved_target_id=can_work.work_id).count() == 1

    # 6. Assert IdentifierAlias marked SUPERSEDED
    alias = IdentifierAlias.objects.get(target_id=dup_work.work_id)
    assert alias.status == "SUPERSEDED"

    # 7. Assert IdentityMergeLedger row recorded
    ledger = IdentityMergeLedger.objects.get(from_id=dup_work.work_id, to_id=can_work.work_id)
    assert ledger.op == "MERGE"
    assert ledger.kind == "WORK"
    assert ledger.reason == "REPARSE_DUPLICATE_RAW_BLOB"
    assert ledger.confidence == 1.0

    # 8. Assert CloudEvent emitted to outbox
    event = EventOutbox.objects.filter(
        type="identity.merged.v1",
        subject=f"{dup_work.work_id}->{can_work.work_id}",
    ).first()
    assert event is not None
    assert event.data["from_id"] == dup_work.work_id
    assert event.data["to_id"] == can_work.work_id

    # 9. Assert re-running is a safe no-op
    out_idempotent = io.StringIO()
    call_command("retire_duplicate_works", stdout=out_idempotent)
    assert "No duplicate works found. Nothing to retire." in out_idempotent.getvalue()
