"""Tests for deduplication, auto-merge, and split work operations.

Normative sources:
- docs/mvp/01_corporate_corpus_and_sources.md §2.4 (IBBI copies vs official copies)
- docs/01_master_architecture.md §5.4, §6.3
- docs/mvp/03_data_model_and_contracts.md §3.3
- S05b Directive #7:
  Auto-merge ONLY when court, normalised case number and decision date all match exactly.
  Ambiguous matches (same number, different year or bench) go to review queue with no merge.
"""

from datetime import UTC, date, datetime

import pytest
from django.db import connection

from anchor_lib.ids import mint_id
from parse.citations.dedupe import (
    check_dedupe_match,
    dedupe_and_merge,
    split_work,
)
from parse.models import (
    CitationMention,
    Court,
    IdentifierAlias,
    IdentityMergeLedger,
    LegalCase,
    ParseRun,
    Work,
    WorkCase,
)


@pytest.fixture
def courts() -> dict[str, Court]:
    c_nclt, _ = Court.objects.get_or_create(court_id="crt_IN_NCLT", defaults={"level": "TRIBUNAL"})
    c_mum, _ = Court.objects.get_or_create(
        court_id="crt_IN_NCLT_MUM", defaults={"level": "TRIBUNAL"}
    )
    c_del, _ = Court.objects.get_or_create(
        court_id="crt_IN_NCLT_DEL", defaults={"level": "TRIBUNAL"}
    )
    return {"nclt": c_nclt, "mum": c_mum, "del": c_del}


@pytest.mark.django_db
def test_dedupe_match_exact(courts: dict[str, Court]) -> None:
    # Both works have same court, same decision date, same case number & year
    case1 = LegalCase.objects.create(
        case_id=mint_id("cas"),
        court=courts["mum"],
        case_type="CP (IB)",
        number="149",
        year=2023,
    )
    case2 = LegalCase.objects.create(
        case_id=mint_id("cas"),
        court=courts["mum"],
        case_type="CP (IB)",
        number=" 149 ",
        year=2023,
    )

    work_ibbi = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
        court=courts["mum"],
        decision_date=date(2023, 10, 15),
    )
    WorkCase.objects.create(work=work_ibbi, case=case1)

    work_official = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
        court=courts["mum"],
        decision_date=date(2023, 10, 15),
    )
    WorkCase.objects.create(work=work_official, case=case2)

    can_merge, status, details = check_dedupe_match(work_ibbi, work_official)
    assert can_merge is True
    assert status == "EXACT_MATCH"


@pytest.mark.django_db
def test_dedupe_match_ambiguous_different_year(courts: dict[str, Court]) -> None:
    # Same number, but different year
    case1 = LegalCase.objects.create(
        case_id=mint_id("cas"), court=courts["mum"], number="149", year=2023
    )
    case2 = LegalCase.objects.create(
        case_id=mint_id("cas"), court=courts["mum"], number="149", year=2022
    )

    work1 = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
        court=courts["mum"],
        decision_date=date(2023, 10, 15),
    )
    WorkCase.objects.create(work=work1, case=case1)

    work2 = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
        court=courts["mum"],
        decision_date=date(2023, 10, 15),
    )
    WorkCase.objects.create(work=work2, case=case2)

    can_merge, status, details = check_dedupe_match(work1, work2)
    assert can_merge is False
    assert status == "AMBIGUOUS"
    assert details["reason"] == "YEAR_MISMATCH"


@pytest.mark.django_db
def test_dedupe_match_ambiguous_different_bench(courts: dict[str, Court]) -> None:
    # Same case number, but different NCLT benches (crt_IN_NCLT vs crt_IN_NCLT_MUM)
    case1 = LegalCase.objects.create(
        case_id=mint_id("cas"), court=courts["nclt"], number="149", year=2023
    )
    case2 = LegalCase.objects.create(
        case_id=mint_id("cas"), court=courts["mum"], number="149", year=2023
    )

    work1 = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
        court=courts["nclt"],
        decision_date=date(2023, 10, 15),
    )
    WorkCase.objects.create(work=work1, case=case1)

    work2 = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
        court=courts["mum"],
        decision_date=date(2023, 10, 15),
    )
    WorkCase.objects.create(work=work2, case=case2)

    can_merge, status, details = check_dedupe_match(work1, work2)
    assert can_merge is False
    assert status == "AMBIGUOUS"
    assert details["reason"] == "DIFFERENT_BENCH"


@pytest.mark.django_db
def test_execute_merge_and_split(courts: dict[str, Court]) -> None:
    # Setup matching works
    case1 = LegalCase.objects.create(
        case_id=mint_id("cas"), court=courts["mum"], number="149", year=2023
    )
    case2 = LegalCase.objects.create(
        case_id=mint_id("cas"), court=courts["mum"], number="149", year=2023
    )

    work_from = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
        court=courts["mum"],
        decision_date=date(2023, 10, 15),
    )
    WorkCase.objects.create(work=work_from, case=case1)

    work_to = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
        court=courts["mum"],
        decision_date=date(2023, 10, 15),
    )
    WorkCase.objects.create(work=work_to, case=case2)

    # Add an active alias and a citation mention pointing to work_from
    alias_from = IdentifierAlias.objects.create(
        scheme="ORDER_NO",
        value_normalized="NCLT/MUM/149/2023",
        target_id=work_from.work_id,
        confidence=1.0,
        source="IBBI_CRAWLER",
        trust_tier="T2",
        status="ACTIVE",
        first_seen=datetime.now(UTC),
    )

    from ops.models import PipelineVersion

    pv, _ = PipelineVersion.objects.get_or_create(
        pipeline_version="p1.parser@0.1.0|det_v1",
        defaults={
            "component": "parser",
            "semver": "0.1.0",
            "code_sha": "0" * 40,
        },
    )

    parse_run = ParseRun.objects.create(
        parse_id=mint_id("par"),
        work=work_to,
        expression_key="en",
        doc_type="ORDER",
        pipeline_version=pv,
        raw_ids=[],
        quality={},
        anchor_changes={},
        parsed_doc_uri="s3://test/parsed.json",
        parsed_doc_sha256="xyz",
        gate="PASS",
    )

    mention = CitationMention.objects.create(
        mention_id=mint_id("cm"),
        parse=parse_run,
        citing_work=work_to,
        anchor_id=f"{work_to.work_id}/en#p1",
        raw_text="earlier order",
        mention_kind="CASE_NUMBER",
        scheme="ORDER_NO",
        normalized="NCLT/MUM/149/2023",
        resolved_target_id=work_from.work_id,
        resolution_confidence=1.0,
        resolution_method="ALIAS_EXACT",
    )

    # 1. Execute dedupe_and_merge
    merge_event_id = dedupe_and_merge(
        work_from.work_id, work_to.work_id, reason="IBBI_OFFICIAL_DEDUPE"
    )

    # Assertions on merge:
    work_from.refresh_from_db()
    assert work_from.status == "MERGED"
    assert work_from.merged_into_id == work_to.work_id

    ledger = IdentityMergeLedger.objects.get(event_id=merge_event_id)
    assert ledger.op == "MERGE"
    assert ledger.from_id == work_from.work_id
    assert ledger.to_id == work_to.work_id

    alias_from.refresh_from_db()
    assert alias_from.status == "SUPERSEDED"

    mention.refresh_from_db()
    assert mention.resolved_target_id == work_to.work_id

    # Verify outbox event identity.merged.v1
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, type, source, topic, partition_key, data
            FROM ops.event_outbox
            WHERE type = 'identity.merged.v1' AND partition_key = %s;
            """,
            [work_from.work_id],
        )
        row = cursor.fetchone()
        assert row is not None
        ev_id, ev_type, ev_source, ev_topic, part_key, data = row
        assert ev_type == "identity.merged.v1"
        assert ev_source == "p1/dedupe"
        assert data["from_id"] == work_from.work_id
        assert data["to_id"] == work_to.work_id

    # 2. Execute split_work to revert the merge
    split_event_id = split_work(merge_event_id, reason="ACCIDENTAL_MERGE")

    work_from.refresh_from_db()
    assert work_from.status == "ACTIVE"
    assert work_from.merged_into is None

    split_ledger = IdentityMergeLedger.objects.get(event_id=split_event_id)
    assert split_ledger.op == "SPLIT"
    assert split_ledger.from_id == work_from.work_id
    assert split_ledger.to_id == work_to.work_id

    # Verify outbox event identity.split.v1
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, type, source, topic, partition_key, data
            FROM ops.event_outbox
            WHERE type = 'identity.split.v1' AND partition_key = %s;
            """,
            [work_from.work_id],
        )
        row = cursor.fetchone()
        assert row is not None
        ev_id, ev_type, ev_source, ev_topic, part_key, data = row
        assert ev_type == "identity.split.v1"
        assert ev_source == "p1/dedupe"
