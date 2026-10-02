"""Tests for alias lifecycle: T4 STUB promotion, supersession, merge ledger and re-pointing.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.3
- S05b Directive #4:
  When a T0–T2 alias for the same key arrives later, the T4 row becomes SUPERSEDED,
  the STUB merges into the real work through identity_merge_ledger, and existing
  mentions are re-pointed.
"""

import pytest
from django.db import connection

from anchor_lib.ids import mint_id
from parse.citations.extractor import ExtractedCitation
from parse.citations.resolver import promote_authoritative_alias, resolve_citation
from parse.models import (
    CitationMention,
    IdentifierAlias,
    IdentityMergeLedger,
    ParseRun,
    Work,
)


@pytest.mark.django_db
def test_t4_stub_promoted_and_merged_on_authoritative_alias() -> None:
    from ops.models import PipelineVersion

    pv, _ = PipelineVersion.objects.get_or_create(
        pipeline_version="p1.parser@0.1.0|det_v1",
        defaults={
            "component": "parser",
            "semver": "0.1.0",
            "code_sha": "0" * 40,
        },
    )

    # 1. Setup citing work and parse run
    citing_work = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
    )
    parse_run = ParseRun.objects.create(
        parse_id=mint_id("par"),
        work=citing_work,
        expression_key="en",
        doc_type="ORDER",
        pipeline_version=pv,
        raw_ids=[],
        quality={},
        anchor_changes={},
        parsed_doc_uri="s3://test/parsed.json",
        parsed_doc_sha256="abc",
        gate="PASS",
    )

    # 2. Ingest citation mention which mints a T4 STUB work
    cite = ExtractedCitation(
        mention_id=mint_id("cm"),
        raw_text="(2019) 4 SCC 17",
        anchor_id=f"{citing_work.work_id}/en#p1",
        char_range=(0, 15),
        mention_kind="FULL",
        scheme="SCC",
        normalized="(2019) 4 SCC 17",
        pin={"kind": "NONE", "method": "UNRESOLVED", "confidence": 0.0},
        court_hint=None,
        date_hint="2019",
        temporal_check="OK",
        quote_selector={"exact": "(2019) 4 SCC 17", "prefix": "", "suffix": ""},
    )

    stub_target_id, conf, method = resolve_citation(cite, citing_work.work_id)
    assert method == "STUB_MINTED"
    assert stub_target_id is not None
    assert stub_target_id.startswith("wrk_")

    mention_record = CitationMention.objects.create(
        mention_id=cite.mention_id,
        parse=parse_run,
        citing_work=citing_work,
        anchor_id=cite.anchor_id,
        raw_text=cite.raw_text,
        mention_kind=cite.mention_kind,
        scheme=cite.scheme,
        normalized=cite.normalized,
        pin=cite.pin,
        resolved_target_id=stub_target_id,
        resolution_confidence=conf,
        resolution_method=method,
        temporal_check=cite.temporal_check,
    )

    # Verify initial T4 alias is ACTIVE
    t4_alias = IdentifierAlias.objects.get(scheme="SCC", value_normalized="(2019) 4 SCC 17")
    assert t4_alias.trust_tier == "T4"
    assert t4_alias.status == "ACTIVE"
    assert t4_alias.target_id == stub_target_id

    # 3. Later, an authoritative T1 judgment work arrives
    authoritative_work = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
        title="Swiss Ribbons Pvt. Ltd. v. Union of India",
    )

    # Promote authoritative alias
    promote_authoritative_alias(
        scheme="SCC",
        value_normalized="(2019) 4 SCC 17",
        authoritative_target_id=authoritative_work.work_id,
        trust_tier="T1",
        source="SCC_REPORTER_METADATA",
    )

    # 4. Assertions:
    # a. T4 alias became SUPERSEDED
    t4_alias.refresh_from_db()
    assert t4_alias.status == "SUPERSEDED"

    # b. New T1 alias is ACTIVE
    auth_alias = IdentifierAlias.objects.get(
        scheme="SCC",
        value_normalized="(2019) 4 SCC 17",
        status="ACTIVE",
    )
    assert auth_alias.trust_tier == "T1"
    assert auth_alias.target_id == authoritative_work.work_id
    assert auth_alias.source == "SCC_REPORTER_METADATA"

    # c. STUB work merged into authoritative work
    old_stub_work = Work.objects.get(work_id=stub_target_id)
    assert old_stub_work.status == "MERGED"
    assert old_stub_work.merged_into_id == authoritative_work.work_id

    # d. IdentityMergeLedger recorded the merge
    ledger_entry = IdentityMergeLedger.objects.get(
        from_id=stub_target_id, to_id=authoritative_work.work_id
    )
    assert ledger_entry.kind == "WORK"
    assert ledger_entry.op == "MERGE"
    assert ledger_entry.reason == "AUTHORITATIVE_ALIAS_PROMOTION"
    assert ledger_entry.confidence == 1.0

    # e. Citation mentions were re-pointed to authoritative work
    mention_record.refresh_from_db()
    assert mention_record.resolved_target_id == authoritative_work.work_id
    assert mention_record.resolution_method == "ALIAS_EXACT"

    # f. Event identity.merged.v1 published to ops.event_outbox
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, type, source, topic, partition_key, dataclass, data
            FROM ops.event_outbox
            WHERE type = 'identity.merged.v1' AND partition_key = %s;
            """,
            [stub_target_id],
        )
        row = cursor.fetchone()
        assert row is not None
        ev_id, ev_type, ev_source, ev_topic, part_key, dataclass, data = row
        assert ev_type == "identity.merged.v1"
        assert ev_source == "p1/citations"
        assert ev_topic == "plc.identity.merged.v1"
        assert data["from_id"] == stub_target_id
        assert data["to_id"] == authoritative_work.work_id
        assert data["reason"] == "AUTHORITATIVE_ALIAS_PROMOTION"
