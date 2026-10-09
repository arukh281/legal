"""Tests for Phase P8 Verification Engine (Ladder C0, C1, C2).

Normative sources:
- docs/mvp/00_mvp_spec.md §4.1
- docs/mvp/03_data_model_and_contracts.md §3.12 (tpl.verification_report, tpl.claim_verification)
- docs/10_P8_verification_evaluation.md §5.3, §5.4
- DECISIONS.md (2026-10-10 S07 Directives):
  - Amendment #1: Display band labelled "quote verified · uncalibrated preview", never plain VERIFIED.
  - Amendment #3: Verifier strictly rejects any claim anchor not in this query's EvidenceBundle.
"""

from __future__ import annotations

import datetime

import pytest
from django.db import connection

from anchor_lib.ids import mint_id
from ops.models import PipelineVersion
from parse.models import Anchor, Work
from reason.models import Claim
from retrieve.models import EvidenceBundle
from verify.models import ClaimVerification
from verify.verifier import VerificationEngine
from workspace.authz import ExecutionContext


@pytest.fixture
def auth_ctx() -> ExecutionContext:
    return ExecutionContext(
        user_id="usr_01M3TESTUSER00000000000000",
        tenant_id="ten_01M3TESTTENANT00000000000",
        firm_role="PARTNER",
        residency_policy="ANY",
        purpose="MATTER_WORK",
    )


@pytest.fixture
def sample_work_and_anchor(db: None) -> tuple[Work, Anchor]:
    """Create test work and anchor in plc schema."""
    work_id = mint_id("wrk")
    work = Work.objects.create(
        work_id=work_id,
        work_type="JUDGMENT",
        court_id="crt_IN_NCLT_MUM",
        decision_date=datetime.date(2026, 9, 24),
        title="Test Company Petition Order",
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
    return work, anchor


@pytest.mark.django_db
def test_verifier_passes_exact_quote_with_uncalibrated_preview_band(
    auth_ctx: ExecutionContext,
    sample_work_and_anchor: tuple[Work, Anchor],
) -> None:
    """Amendment #1: Verified claims get display band 'quote verified · uncalibrated preview'."""
    work, anchor = sample_work_and_anchor

    with connection.cursor() as cur:
        cur.execute("SET LOCAL app.tenant_id = %s;", [auth_ctx.tenant_id])

    query_id = mint_id("qry")
    bundle = EvidenceBundle(
        tenant_id=auth_ctx.tenant_id,
        bundle_id=mint_id("evb"),
        query_id=query_id,
        as_of_legal_date=datetime.date(2026, 10, 1),
        index_generation="g1",
        pipeline_version=PipelineVersion.objects.first(),
        items=[{"item_id": "item_1", "anchor_ids": [anchor.anchor_id]}],
        coverage={},
        trace_id="trace_test",
    )

    claim = Claim.objects.create(
        tenant_id=auth_ctx.tenant_id,
        claim_id=mint_id("clm"),
        owner_kind="ANSWER",
        owner_id=query_id,
        text="The enquiry under Section 7 is confined to financial debt and default.",
        claim_type="LEGAL_PROPOSITION",
        support=[
            {
                "anchor_id": anchor.anchor_id,
                "quote": "scope of enquiry under Section 7 of the Insolvency and Bankruptcy Code, 2016 is limited to ascertaining the existence of a financial debt and the occurrence of default",
                "span": [0, 100],
                "support_type": "DIRECT",
            }
        ],
    )

    verifier = VerificationEngine()
    report = verifier.verify(query_id=query_id, claims=[claim], bundle=bundle, ctx=auth_ctx)

    assert report.report_id.startswith("vr_")
    assert report.gate == "PASS"

    claim_ver = ClaimVerification.objects.filter(
        tenant_id=auth_ctx.tenant_id, report_id=report.report_id, claim_id=claim.claim_id
    ).first()
    assert claim_ver is not None
    assert claim_ver.status == "VERIFIED"
    # DB enum band is VERIFIED with confidence_stratum UNCALIBRATED_PREVIEW (03 §3.12)
    assert claim_ver.display_band == "VERIFIED"
    assert claim_ver.confidence_stratum == "UNCALIBRATED_PREVIEW"
    assert claim_ver.warrant["exists"] == "PASS"
    assert claim_ver.warrant["quote_exact"] == "PASS"


@pytest.mark.django_db
def test_verifier_rejects_out_of_bundle_anchor(
    auth_ctx: ExecutionContext,
    sample_work_and_anchor: tuple[Work, Anchor],
) -> None:
    """Amendment #3: Verifier strictly rejects any claim anchor not present in this query's EvidenceBundle."""
    work, anchor = sample_work_and_anchor

    with connection.cursor() as cur:
        cur.execute("SET LOCAL app.tenant_id = %s;", [auth_ctx.tenant_id])

    query_id = mint_id("qry")
    # Bundle contains a DIFFERENT anchor, not anchor.anchor_id
    bundle = EvidenceBundle(
        tenant_id=auth_ctx.tenant_id,
        bundle_id=mint_id("evb"),
        query_id=query_id,
        as_of_legal_date=datetime.date(2026, 10, 1),
        index_generation="g1",
        pipeline_version=PipelineVersion.objects.first(),
        items=[{"item_id": "item_1", "anchor_ids": ["wrk_01M3OTHER0000000000000000/en#p1"]}],
        coverage={},
        trace_id="trace_test",
    )

    claim = Claim.objects.create(
        tenant_id=auth_ctx.tenant_id,
        claim_id=mint_id("clm"),
        owner_kind="ANSWER",
        owner_id=query_id,
        text="Some proposition.",
        claim_type="LEGAL_PROPOSITION",
        support=[
            {
                "anchor_id": anchor.anchor_id,
                "quote": "scope of enquiry",
                "span": [0, 16],
                "support_type": "DIRECT",
            }
        ],
    )

    verifier = VerificationEngine()
    report = verifier.verify(query_id=query_id, claims=[claim], bundle=bundle, ctx=auth_ctx)

    claim_ver = ClaimVerification.objects.filter(
        tenant_id=auth_ctx.tenant_id, report_id=report.report_id, claim_id=claim.claim_id
    ).first()
    assert claim_ver is not None
    assert claim_ver.status == "UNSUPPORTED"
    assert claim_ver.display_band == "WITHHELD"
    assert "OUT_OF_BUNDLE" in claim_ver.reason_codes
    assert claim.claim_id in report.withheld_claim_ids


@pytest.mark.django_db
def test_verifier_rejects_misquoted_claim(
    auth_ctx: ExecutionContext,
    sample_work_and_anchor: tuple[Work, Anchor],
) -> None:
    """C2 check: Verifier rejects claim when quote is not an exact substring of anchor text."""
    work, anchor = sample_work_and_anchor

    with connection.cursor() as cur:
        cur.execute("SET LOCAL app.tenant_id = %s;", [auth_ctx.tenant_id])

    query_id = mint_id("qry")
    bundle = EvidenceBundle(
        tenant_id=auth_ctx.tenant_id,
        bundle_id=mint_id("evb"),
        query_id=query_id,
        as_of_legal_date=datetime.date(2026, 10, 1),
        index_generation="g1",
        pipeline_version=PipelineVersion.objects.first(),
        items=[{"item_id": "item_1", "anchor_ids": [anchor.anchor_id]}],
        coverage={},
        trace_id="trace_test",
    )

    claim = Claim.objects.create(
        tenant_id=auth_ctx.tenant_id,
        claim_id=mint_id("clm"),
        owner_kind="ANSWER",
        owner_id=query_id,
        text="A misquoted proposition.",
        claim_type="LEGAL_PROPOSITION",
        support=[
            {
                "anchor_id": anchor.anchor_id,
                "quote": "THIS TEXT DOES NOT EXIST IN THE REAL COURT ANCHOR AT ALL",
                "span": [0, 50],
                "support_type": "DIRECT",
            }
        ],
    )

    verifier = VerificationEngine()
    report = verifier.verify(query_id=query_id, claims=[claim], bundle=bundle, ctx=auth_ctx)

    claim_ver = ClaimVerification.objects.filter(
        tenant_id=auth_ctx.tenant_id, report_id=report.report_id, claim_id=claim.claim_id
    ).first()
    assert claim_ver is not None
    assert claim_ver.status == "UNSUPPORTED"
    assert claim_ver.display_band == "WITHHELD"
    assert "MISQUOTE" in claim_ver.reason_codes
    assert claim_ver.warrant["quote_exact"] == "FAIL"


@pytest.mark.django_db
def test_verifier_rejects_fabricated_anchor(
    auth_ctx: ExecutionContext,
) -> None:
    """C1 check: Verifier rejects anchor that does not exist in plc.anchor."""
    with connection.cursor() as cur:
        cur.execute("SET LOCAL app.tenant_id = %s;", [auth_ctx.tenant_id])

    fake_work_id = mint_id("wrk")
    fake_anchor_id = f"{fake_work_id}/en#p999"
    query_id = mint_id("qry")
    bundle = EvidenceBundle(
        tenant_id=auth_ctx.tenant_id,
        bundle_id=mint_id("evb"),
        query_id=query_id,
        as_of_legal_date=datetime.date(2026, 10, 1),
        index_generation="g1",
        pipeline_version=PipelineVersion.objects.first(),
        items=[{"item_id": "item_1", "anchor_ids": [fake_anchor_id]}],
        coverage={},
        trace_id="trace_test",
    )

    claim = Claim.objects.create(
        tenant_id=auth_ctx.tenant_id,
        claim_id=mint_id("clm"),
        owner_kind="ANSWER",
        owner_id=query_id,
        text="Fabricated citation proposition.",
        claim_type="LEGAL_PROPOSITION",
        support=[
            {
                "anchor_id": fake_anchor_id,
                "quote": "some quote",
                "span": [0, 10],
                "support_type": "DIRECT",
            }
        ],
    )

    verifier = VerificationEngine()
    report = verifier.verify(query_id=query_id, claims=[claim], bundle=bundle, ctx=auth_ctx)

    claim_ver = ClaimVerification.objects.filter(
        tenant_id=auth_ctx.tenant_id, report_id=report.report_id, claim_id=claim.claim_id
    ).first()
    assert claim_ver is not None
    assert claim_ver.status == "UNSUPPORTED"
    assert "FABRICATED_ANCHOR" in claim_ver.reason_codes
    assert claim_ver.warrant["exists"] == "FAIL"
