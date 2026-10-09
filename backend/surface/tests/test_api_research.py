"""Tests for Surface REST API: Research Q&A and Document Source Viewer.

Normative sources:
- docs/mvp/00_mvp_spec.md §4.1
- docs/mvp/03_data_model_and_contracts.md §3.11, §3.12
- DECISIONS.md (2026-10-10 S07 Directives)
"""

from __future__ import annotations

import datetime
import json
from collections.abc import Generator
from typing import Any

import pytest
from django.db import connections
from django.test import Client

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from gateway.adapters.fake import FakeModelAdapter
from gateway.runner import set_adapter_override
from index.tests.test_ial import _insert_chunk
from parse.models import Anchor, Work
from workspace.models import AppUser, Tenant

pytestmark = pytest.mark.django_db(databases="__all__", transaction=True)


@pytest.fixture(autouse=True)
def enable_dev_auth_in_tests(settings: Any) -> None:
    settings.DEBUG = True
    settings.DEV_AUTH_ENABLED = True


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
def test_setup() -> dict[str, Any]:
    t_id = mint_id("ten")
    u_id = mint_id("usr")
    w_id = mint_id("wrk")
    user_email = f"associate_{u_id}@firm.in"

    with admin_db_context():
        tenant = Tenant.objects.create(
            tenant_id=t_id,
            name="Partner Firm LLP",
            deployment_mode="D2",
            residency_policy="ANY",
            idp={"kind": "GOOGLE"},
        )
        user = AppUser.objects.create(
            tenant_id=t_id,
            user_id=u_id,
            email=user_email,
            idp_subject=f"idp_sub_{u_id}",
            firm_role="ASSOCIATE",
            active=True,
        )

    work = Work.objects.create(
        work_id=w_id,
        work_type="JUDGMENT",
        court_id="crt_IN_NCLT_MUM",
        decision_date=datetime.date(2026, 9, 24),
        title="Tribute Trading and Finance Limited v. Florin Real Estate",
        status="ACTIVE",
    )
    anchor = Anchor.objects.create(
        anchor_id=f"{work.work_id}/en#p6",
        work_id=work.work_id,
        expression_key="en",
        fragment="p6",
        node_type="PARA",
        text="6.1. It is pertinent to note that the scope of enquiry under Section 7 of the Insolvency and Bankruptcy Code, 2016 is limited to ascertaining the existence of a financial debt and the occurrence of default.",
        text_hash="hash_p6",
        ocr_conf=1.0,
        lang="en",
        is_authoritative_expression=True,
        state="LIVE",
        first_parse_id="par_test",
        last_parse_id="par_test",
    )

    _insert_chunk(
        chunk_id=mint_id("chk"),
        work_id=work.work_id,
        anchor_ids=[anchor.anchor_id],
        context_header="Tribute Trading v. Florin Real Estate",
        text="scope of enquiry under Section 7 of the Insolvency and Bankruptcy Code, 2016 is limited to ascertaining the existence of a financial debt and default",
    )

    return {"tenant": tenant, "user": user, "work": work, "anchor": anchor}


@pytest.fixture
def fake_adapter() -> Generator[FakeModelAdapter]:
    adapter = FakeModelAdapter()
    set_adapter_override("fake", adapter)
    set_adapter_override("anthropic", adapter)
    yield adapter
    set_adapter_override("fake", None)
    set_adapter_override("anthropic", None)


def test_research_query_endpoint_unauthenticated_fails(client: Client) -> None:
    """Endpoint refuses unauthenticated requests with 401."""
    res = client.post(
        "/api/research/query",
        data=json.dumps({"text": "Section 7 scope"}),
        content_type="application/json",
    )
    assert res.status_code == 401


def test_research_query_endpoint_end_to_end(
    client: Client,
    test_setup: dict[str, Any],
    fake_adapter: FakeModelAdapter,
) -> None:
    """End-to-end research query returns verified claims, contrary sweep, dynamic date, and degradations."""
    anchor = test_setup["anchor"]
    user = test_setup["user"]
    # 1. Dev login
    login_res = client.post(
        "/api/auth/dev-login",
        data=json.dumps({"email": user.email}),
        content_type="application/json",
    )
    assert login_res.status_code == 200

    # 2. Queue canned synthesis response
    canned_response = {
        "summary": "Under Section 7, the inquiry is limited to the existence of financial debt and default.",
        "in_corpus": True,
        "claims": [
            {
                "text": "The scope of enquiry under Section 7 of the IBC is limited to debt and default.",
                "claim_type": "LEGAL_PROPOSITION",
                "anchor_id": anchor.anchor_id,
                "quote": "scope of enquiry under Section 7 of the Insolvency and Bankruptcy Code, 2016 is limited to ascertaining the existence of a financial debt and the occurrence of default",
                "support_type": "DIRECT",
            }
        ],
        "contrary_sweep": {
            "status": "LIMITED",
            "notes": "lexical only, no citator",
        },
    }
    fake_adapter.queue_response(json.dumps(canned_response))

    # 3. Post query
    res = client.post(
        "/api/research/query",
        data=json.dumps({"text": "scope of enquiry under Section 7"}),
        content_type="application/json",
    )
    assert res.status_code == 200
    data = res.json()

    assert data["query_id"].startswith("qry_")
    assert data["in_corpus"] is True
    assert "Section 7" in data["summary"]

    # Amendment #1 & #2 assertions
    assert len(data["claims"]) == 1
    claim = data["claims"][0]
    assert claim["verification_status"] == "VERIFIED"
    assert claim["display_band"] == "quote verified · uncalibrated preview"
    assert claim["support"][0]["anchor_id"] == anchor.anchor_id

    assert data["contrary_sweep"]["status"] == "LIMITED"
    assert "lexical only" in data["contrary_sweep"]["notes"]

    # Amendment #7: dynamic date
    assert data["law_current_to"] >= "2026-10-01"

    # Degradations disclosure
    assert len(data["degradations"]) > 0
    assert data["degradations"][0]["kind"] == "INDEX_LAG"


def test_anchor_source_endpoint(
    client: Client,
    test_setup: dict[str, Any],
) -> None:
    """GET /api/documents/anchor/{anchor_id} returns exact text and court metadata for click-to-source."""
    anchor = test_setup["anchor"]
    # Dev login
    client.post(
        "/api/auth/dev-login",
        data=json.dumps({"email": test_setup["user"].email}),
        content_type="application/json",
    )

    res = client.get("/api/research/documents/anchor", {"anchor_id": anchor.anchor_id})
    assert res.status_code == 200
    data = res.json()

    assert data["anchor_id"] == anchor.anchor_id
    assert data["work_id"] == anchor.work_id
    assert "scope of enquiry under Section 7" in data["text"]
    assert data["court_id"] == "crt_IN_NCLT_MUM"
    assert data["ocr_conf"] == 1.0


def test_document_source_endpoint(
    client: Client,
    test_setup: dict[str, Any],
) -> None:
    """GET /api/documents/{work_id}/source returns all paragraphs for full judgment viewing."""
    work = test_setup["work"]
    # Dev login
    client.post(
        "/api/auth/dev-login",
        data=json.dumps({"email": test_setup["user"].email}),
        content_type="application/json",
    )

    res = client.get(f"/api/research/documents/{work.work_id}/source")
    assert res.status_code == 200
    data = res.json()

    assert data["work_id"] == work.work_id
    assert data["court_id"] == "crt_IN_NCLT_MUM"
    assert len(data["paragraphs"]) > 0
    first_p = data["paragraphs"][0]
    assert first_p["fragment"] == "p6"
    assert "scope of enquiry" in first_p["text"]
