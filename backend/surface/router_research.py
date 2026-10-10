"""Ninja Router for Research Q&A and Document Source Viewer (Surface P10).

Normative sources:
- docs/mvp/00_mvp_spec.md §4.1 (Research Q&A, source viewer)
- docs/mvp/03_data_model_and_contracts.md §3.11, §3.12
- docs/12_P10_product_surface.md §2.1
- DECISIONS.md (2026-10-10 S07 Directives)
"""

from __future__ import annotations

import datetime
from typing import Any, cast

from django.http import HttpRequest
from ninja import Router, Schema
from ninja.errors import HttpError

from anchor_lib.ids import mint_id
from core.authz_dependency import authz_required
from parse.models import Anchor, Work
from reason.synthesizer import AnswerSynthesizer
from retrieve.models import ResearchQuery
from retrieve.retriever import RetrievalEngine, get_law_current_to_date
from verify.models import ClaimVerification
from verify.verifier import VerificationEngine
from workspace.authz import ExecutionContext

router = Router(tags=["Research & Source Viewer"])


class ResearchQueryRequest(Schema):
    text: str
    mode: str = "STANDARD"
    as_of_legal_date: str | None = None


class ClaimResponseItem(Schema):
    claim_id: str
    text: str
    claim_type: str
    support: list[dict[str, Any]]
    verification_status: str
    display_band: str
    reason_codes: list[str]


class ContrarySweepResponse(Schema):
    status: str
    notes: str


class DegradationItem(Schema):
    kind: str
    detail: str


class ResearchQueryResponse(Schema):
    query_id: str
    text: str
    summary: str
    summary_status: str
    in_corpus: bool
    claims: list[ClaimResponseItem]
    contrary_sweep: ContrarySweepResponse
    law_current_to: str
    degradations: list[DegradationItem]
    verification_gate: str
    created_at: str


class AnchorSourceResponse(Schema):
    anchor_id: str
    work_id: str
    fragment: str
    number_as_printed: str | None
    node_type: str
    text: str
    ocr_conf: float | None
    title: str | None
    court_id: str | None
    decision_date: str | None


class DocumentParagraphItem(Schema):
    anchor_id: str
    fragment: str
    number_as_printed: str | None
    node_type: str
    text: str
    ocr_conf: float | None


class DocumentSourceResponse(Schema):
    work_id: str
    title: str | None
    court_id: str | None
    decision_date: str | None
    status: str
    paragraphs: list[DocumentParagraphItem]


@router.post("/query", response=ResearchQueryResponse, auth=authz_required)
def execute_research_query(
    request: HttpRequest,
    payload: ResearchQueryRequest,
) -> dict[str, Any]:
    """Execute end-to-end legal research Q&A with claim-level verification and contrary sweep."""
    ctx: ExecutionContext = cast(Any, request).auth_ctx

    # Determine legal date
    if payload.as_of_legal_date:
        try:
            legal_date = datetime.date.fromisoformat(payload.as_of_legal_date)
        except ValueError as exc:
            raise HttpError(400, "Invalid as_of_legal_date format. Use YYYY-MM-DD.") from exc
    else:
        legal_date = get_law_current_to_date()

    query_id = mint_id("qry")
    query = ResearchQuery(
        tenant_id=ctx.tenant_id,
        query_id=query_id,
        matter_id=ctx.matter_id,
        user_id=ctx.user_id,
        text=payload.text.strip(),
        mode=payload.mode if payload.mode in ["QUICK", "STANDARD", "DEEP"] else "STANDARD",
        as_of_legal_date=legal_date,
        perspective="NEUTRAL",
        stance_target="BOTH",
        request={"raw_input": payload.text},
    )
    query.save()

    # 1. P5 Retrieval
    retriever = RetrievalEngine(index_family="plc_chunks")
    bundle = retriever.retrieve(query=query, ctx=ctx, k=15)

    # 2. P6 Synthesis
    synthesizer = AnswerSynthesizer()
    synthesis_output, claims = synthesizer.synthesize(query=query, bundle=bundle, ctx=ctx)

    # 3. P8 Verification
    verifier = VerificationEngine()
    report = verifier.verify(query_id=query_id, claims=claims, bundle=bundle, ctx=ctx)

    # 4. Assemble response
    verifications = ClaimVerification.objects.filter(
        tenant_id=ctx.tenant_id,
        report_id=report.report_id,
    )
    ver_by_claim_id = {v.claim_id: v for v in verifications}

    formatted_claims: list[dict[str, Any]] = []
    for c in claims:
        v_info = ver_by_claim_id.get(c.claim_id)
        if v_info and v_info.display_band == "VERIFIED":
            band_label = "quote verified · uncalibrated preview"
        elif v_info:
            band_label = v_info.display_band
        else:
            band_label = "WITHHELD"

        formatted_claims.append(
            {
                "claim_id": c.claim_id,
                "text": c.text,
                "claim_type": c.claim_type,
                "support": c.support,
                "verification_status": v_info.status if v_info else "UNVERIFIABLE",
                "display_band": band_label,
                "reason_codes": v_info.reason_codes if v_info else [],
            }
        )

    contrary_sweep_data = synthesis_output.get("contrary_sweep", {})
    if not contrary_sweep_data or contrary_sweep_data.get("status") != "NOT_IN_CORPUS":
        contrary_sweep_data = {
            "status": "LIMITED",
            "notes": "lexical only, no citator",
        }

    summary_status = "unverified summary" if synthesis_output.get("in_corpus", True) else "out of corpus"

    answer_payload = {
        "summary": synthesis_output.get("summary", ""),
        "summary_status": summary_status,
        "in_corpus": synthesis_output.get("in_corpus", True),
        "claims": formatted_claims,
        "contrary_sweep": contrary_sweep_data,
        "law_current_to": legal_date.isoformat(),
        "degradations": report.degradations,
        "verification_gate": report.gate,
    }

    query.answer = answer_payload
    query.verification_report_id = report.report_id
    query.save()

    return {
        "query_id": query_id,
        "text": query.text,
        "summary": answer_payload["summary"],
        "summary_status": summary_status,
        "in_corpus": answer_payload["in_corpus"],
        "claims": formatted_claims,
        "contrary_sweep": contrary_sweep_data,
        "law_current_to": legal_date.isoformat(),
        "degradations": report.degradations,
        "verification_gate": report.gate,
        "created_at": query.created_at.isoformat(),
    }


@router.get("/documents/anchor", response=AnchorSourceResponse, auth=authz_required)
def get_anchor_source(request: HttpRequest, anchor_id: str) -> dict[str, Any]:
    """Retrieve full text and metadata for a specific pinpoint anchor."""
    try:
        anchor = Anchor.objects.get(anchor_id=anchor_id)
    except Anchor.DoesNotExist as exc:
        raise HttpError(404, f"Anchor '{anchor_id}' not found.") from exc

    work = Work.objects.filter(work_id=anchor.work_id).first()

    return {
        "anchor_id": anchor.anchor_id,
        "work_id": anchor.work_id,
        "fragment": anchor.fragment,
        "number_as_printed": anchor.number_as_printed,
        "node_type": anchor.node_type,
        "text": anchor.text,
        "ocr_conf": anchor.ocr_conf,
        "title": work.title if work else None,
        "court_id": work.court_id if work else None,
        "decision_date": work.decision_date.isoformat() if work and work.decision_date else None,
    }


@router.get("/documents/{work_id}/source", response=DocumentSourceResponse, auth=authz_required)
def get_document_source(request: HttpRequest, work_id: str) -> dict[str, Any]:
    """Retrieve all ordered paragraphs and metadata for source document inspection."""
    work = Work.objects.filter(work_id=work_id).first()
    if not work:
        raise HttpError(404, f"Work '{work_id}' not found.")

    anchors = Anchor.objects.filter(work_id=work_id, state="LIVE")
    paragraphs = [
        {
            "anchor_id": a.anchor_id,
            "fragment": a.fragment,
            "number_as_printed": a.number_as_printed,
            "node_type": a.node_type,
            "text": a.text,
            "ocr_conf": a.ocr_conf,
        }
        for a in anchors
    ]

    return {
        "work_id": work.work_id,
        "title": work.title,
        "court_id": work.court_id,
        "decision_date": work.decision_date.isoformat() if work.decision_date else None,
        "status": work.status,
        "paragraphs": paragraphs,
    }
