"""Tests for citation resolver: alias lookup, STUB work vs STUB case minting, and T4 trust tier.

Normative sources:
- docs/03_P1_ingestion_parsing.md §5.9
- docs/mvp/03_data_model_and_contracts.md §3.3
- S05b Directives:
  - Reporter mints STUB Work
  - Case number mints STUB LegalCase (never STUB work)
  - Case number without court stated stays UNRESOLVED (no stub minted)
  - Trust tier T4 for citation-derived aliases with source="citation_mention" and evidence dict
  - acquire.requested.v1 event emission with full contract
"""

import pytest
from django.db import connection

from anchor_lib.ids import mint_id
from parse.citations.extractor import ExtractedCitation
from parse.citations.resolver import resolve_citation
from parse.models import Court, IdentifierAlias, LegalCase, Work


@pytest.mark.django_db
def test_resolve_reporter_mints_stub_work() -> None:
    # Setup test citing work
    court, _ = Court.objects.get_or_create(
        court_id="crt_IN_SC",
        defaults={"level": "SC"},
    )
    citing_work = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
        court=court,
    )

    cite = ExtractedCitation(
        mention_id=mint_id("cm"),
        raw_text="(2019) 4 SCC 17",
        anchor_id=f"{citing_work.work_id}/en#p1",
        char_range=(10, 24),
        mention_kind="FULL",
        scheme="SCC",
        normalized="(2019) 4 SCC 17",
        pin={"kind": "NONE", "method": "UNRESOLVED", "confidence": 0.0},
        court_hint=None,
        date_hint="2019",
        temporal_check="OK",
        quote_selector={"exact": "(2019) 4 SCC 17", "prefix": "", "suffix": ""},
    )

    target_id, conf, method = resolve_citation(cite, citing_work.work_id)

    assert method == "STUB_MINTED"
    assert target_id is not None
    assert target_id.startswith("wrk_")

    # Verify STUB work in DB
    stub_work = Work.objects.get(work_id=target_id)
    assert stub_work.status == "STUB"
    assert stub_work.work_type == "JUDGMENT"

    # Verify T4 Alias in DB (Directive #4)
    alias = IdentifierAlias.objects.get(scheme="SCC", value_normalized="(2019) 4 SCC 17")
    assert alias.target_id == target_id
    assert alias.trust_tier == "T4"
    assert alias.source == "citation_mention"
    assert alias.status == "ACTIVE"
    assert alias.evidence == {
        "mention_id": cite.mention_id,
        "citing_work_id": citing_work.work_id,
        "anchor_id": cite.anchor_id,
    }

    # Verify outbox event acquire.requested.v1
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, type, source, topic, partition_key, dataclass, data
            FROM ops.event_outbox
            WHERE type = 'acquire.requested.v1' AND partition_key = %s;
            """,
            [f"SCC|{cite.normalized}"],
        )
        row = cursor.fetchone()
        assert row is not None
        ev_id, ev_type, ev_source, ev_topic, part_key, dataclass, data = row
        assert ev_type == "acquire.requested.v1"
        assert ev_source == "p1/citations"
        assert ev_topic == "plc.acquire.requested.v1"
        assert dataclass == "PUBLIC"
        assert data["reason"] == "UNRESOLVED_CITATION"
        assert data["target"]["scheme"] == "SCC"
        assert data["target"]["value"] == "(2019) 4 SCC 17"

    # Second resolution of the same citation should hit the existing STUB alias
    target_id2, conf2, method2 = resolve_citation(cite, citing_work.work_id)
    assert target_id2 == target_id
    assert method2 == "ALIAS_EXACT"


@pytest.mark.django_db
def test_resolve_case_number_mints_stub_case() -> None:
    court, _ = Court.objects.get_or_create(
        court_id="crt_IN_NCLT",
        defaults={"level": "TRIBUNAL"},
    )
    citing_work = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
        court=court,
    )

    cite = ExtractedCitation(
        mention_id=mint_id("cm"),
        raw_text="Company Petition (IB) No. 149 of 2023",
        anchor_id=f"{citing_work.work_id}/en#p2",
        char_range=(0, 37),
        mention_kind="CASE_NUMBER",
        scheme="CASE_NO",
        normalized="crt_IN_NCLT|CP (IB)|149|2023",
        pin={"kind": "NONE", "method": "UNRESOLVED", "confidence": 0.0},
        court_hint="crt_IN_NCLT",
        date_hint="2023",
        temporal_check="OK",
        quote_selector={
            "exact": "Company Petition (IB) No. 149 of 2023",
            "prefix": "",
            "suffix": "",
        },
    )

    target_id, conf, method = resolve_citation(cite, citing_work.work_id)

    assert method == "STUB_MINTED"
    assert target_id is not None
    # Directive #2: Case numbers mint STUB cases, NOT judgment works!
    assert target_id.startswith("cas_")
    assert not target_id.startswith("wrk_")

    stub_case = LegalCase.objects.get(case_id=target_id)
    assert stub_case.status == "STUB"
    assert stub_case.court_id == "crt_IN_NCLT"
    assert stub_case.case_type == "CP (IB)"
    assert stub_case.number == "149"
    assert stub_case.year == 2023

    # Verify T4 Alias
    alias = IdentifierAlias.objects.get(
        scheme="CASE_NO", value_normalized="crt_IN_NCLT|CP (IB)|149|2023"
    )
    assert alias.target_id == target_id
    assert alias.trust_tier == "T4"
    assert alias.source == "citation_mention"


@pytest.mark.django_db
def test_case_number_without_court_stays_unresolved() -> None:
    citing_work = Work.objects.create(
        work_id=mint_id("wrk"),
        work_type="JUDGMENT",
        status="ACTIVE",
    )

    # Citation without court
    cite = ExtractedCitation(
        mention_id=mint_id("cm"),
        raw_text="Civil Appeal No. 2594 of 2026",
        anchor_id=f"{citing_work.work_id}/en#p3",
        char_range=(0, 29),
        mention_kind="CASE_NUMBER",
        scheme="CASE_NO",
        normalized="|Civil Appeal|2594|2026",
        pin={"kind": "NONE", "method": "UNRESOLVED", "confidence": 0.0},
        court_hint=None,
        date_hint="2026",
        temporal_check="OK",
        quote_selector={"exact": "Civil Appeal No. 2594 of 2026", "prefix": "", "suffix": ""},
    )

    # Directive #4: If the court isn't stated in the citation, don't mint an alias or a STUB case.
    # Leave the mention UNRESOLVED.
    target_id, conf, method = resolve_citation(cite, citing_work.work_id)

    assert target_id is None
    assert method == "UNRESOLVED"
    assert not IdentifierAlias.objects.filter(value_normalized="|Civil Appeal|2594|2026").exists()
    assert not LegalCase.objects.filter(number="2594", year=2026).exists()
