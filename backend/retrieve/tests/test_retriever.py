"""Tests for Phase P5 Retrieval Engine.

Normative sources:
- docs/mvp/00_mvp_spec.md §4.1
- docs/mvp/03_data_model_and_contracts.md §3.11
- DECISIONS.md (2026-10-10 S07 Directives)
"""

from __future__ import annotations

import datetime

import pytest
from django.db import connections

from anchor_lib.ids import mint_id
from index.tests.test_ial import _insert_chunk
from retrieve.models import EvidenceBundle, ResearchQuery
from retrieve.retriever import RetrievalEngine, get_law_current_to_date
from workspace.authz import ExecutionContext
from workspace.db import tenant_db_context

pytestmark = pytest.mark.django_db(databases=["default", "owner"], transaction=True)


@pytest.fixture(autouse=True)
def setup_index_alias() -> None:
    with connections["owner"].cursor() as cur:
        cur.execute(
            """
            UPDATE ops.index_generation
            SET state = 'LIVE', promoted_at = now()
            WHERE index_family = 'plc_chunks' AND generation = 'g1';
            """
        )
        cur.execute(
            """
            INSERT INTO ops.index_alias (index_family, generation, swapped_at)
            VALUES ('plc_chunks', 'g1', now())
            ON CONFLICT (index_family) DO UPDATE SET generation = 'g1';
            """
        )


@pytest.fixture
def auth_ctx() -> ExecutionContext:
    return ExecutionContext(
        user_id="usr_01M3TESTUSER00000000000000",
        tenant_id="ten_01M3TESTTENANT00000000000",
        firm_role="PARTNER",
        residency_policy="ANY",
        purpose="MATTER_WORK",
    )


def test_law_current_to_date_dynamic() -> None:
    """Amendment #7: law_current_to is dynamically derived from latest capture date."""
    d = get_law_current_to_date()
    assert isinstance(d, datetime.date)
    assert d >= datetime.date(2026, 10, 1)


def test_retrieve_evidence_bundle(auth_ctx: ExecutionContext) -> None:
    """Retrieve evidence bundle returns typed items with contrary sweep LIMITED."""
    test_work_id = mint_id("wrk")
    _insert_chunk(
        chunk_id="chk_test_s7",
        work_id=test_work_id,
        anchor_ids=[f"{test_work_id}/en#p6"],
        context_header="NCLT Mumbai Order",
        text="Section 7 financial creditor default scope of enquiry",
    )

    with tenant_db_context(tenant_id=auth_ctx.tenant_id, user_id=auth_ctx.user_id):
        query = ResearchQuery.objects.create(
            tenant_id=auth_ctx.tenant_id,
            query_id=mint_id("qry"),
            user_id=auth_ctx.user_id,
            text="Section 7 financial creditor",
            mode="STANDARD",
            as_of_legal_date=get_law_current_to_date(),
            perspective="NEUTRAL",
            stance_target="BOTH",
        )

        retriever = RetrievalEngine(index_family="plc_chunks")
        bundle = retriever.retrieve(query=query, ctx=auth_ctx, k=5)

    assert bundle.bundle_id.startswith("evb_")
    assert bundle.query_id == query.query_id
    assert bundle.index_generation == "g1"
    assert len(bundle.items) > 0

    # Verify first item structure
    first_item = bundle.items[0]
    assert "item_id" in first_item
    assert len(first_item["anchor_ids"]) > 0
    assert first_item["anchor_ids"][0].startswith("wrk_")
    assert "excerpt" in first_item
    assert len(first_item["excerpt"]) > 0

    # Amendment #2: Contrary sweep reports status LIMITED ("lexical only, no citator")
    coverage = bundle.coverage
    main_coverage = coverage["per_issue"]["main"]
    adverse_search = main_coverage["adverse_search"]
    assert adverse_search["status"] == "LIMITED"
    assert adverse_search["reason"] == "lexical only, no citator"
    assert adverse_search["attested"] is True


def test_retrieve_rls_isolation(auth_ctx: ExecutionContext) -> None:
    """Verify tenant isolation policy on tpl.research_query and tpl.evidence_bundle."""
    test_work_id = mint_id("wrk")
    _insert_chunk(
        chunk_id="chk_test_s9",
        work_id=test_work_id,
        anchor_ids=[f"{test_work_id}/en#p1"],
        context_header="NCLT Order",
        text="Section 9 operational creditor application",
    )

    with tenant_db_context(tenant_id=auth_ctx.tenant_id, user_id=auth_ctx.user_id):
        query = ResearchQuery.objects.create(
            tenant_id=auth_ctx.tenant_id,
            query_id=mint_id("qry"),
            user_id=auth_ctx.user_id,
            text="Section 9 operational creditor",
            mode="STANDARD",
            as_of_legal_date=datetime.date(2026, 10, 1),
        )

        retriever = RetrievalEngine(index_family="plc_chunks")
        bundle = retriever.retrieve(query=query, ctx=auth_ctx, k=2)

        # Within tenant context, rows are visible
        assert ResearchQuery.objects.filter(query_id=query.query_id).exists()
        assert EvidenceBundle.objects.filter(bundle_id=bundle.bundle_id).exists()

    # Under different tenant context, rows are hidden by RLS
    with tenant_db_context(tenant_id="ten_01M3OTHERTENANT0000000000"):
        assert not ResearchQuery.objects.filter(query_id=query.query_id).exists()
        assert not EvidenceBundle.objects.filter(bundle_id=bundle.bundle_id).exists()
