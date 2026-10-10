"""Measure one question through the gateway: latency, finish_reason, and call record."""

# ruff: noqa: E402

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import django

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.local")
django.setup()

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from gateway.models import LLMCallRecord, ModelEndpoint
from reason.synthesizer import AnswerSynthesizer
from retrieve.models import ResearchQuery
from retrieve.retriever import RetrievalEngine, get_law_current_to_date
from workspace.authz import ExecutionContext
from workspace.db import tenant_db_context
from workspace.models import AppUser, Tenant


def main() -> None:
    # 0. Enforce real Gemini endpoint
    with admin_db_context():
        ModelEndpoint.objects.filter(provider="fake").update(health="DOWN")
        ModelEndpoint.objects.filter(endpoint_id="ep_gemini_3_8_flash").update(
            health="UP",
            data_class_max="PUBLIC",
            price={"in_per_mtok": 0.75, "out_per_mtok": 3.75},
        )

    with admin_db_context():
        tenant, _ = Tenant.objects.get_or_create(
            tenant_id="ten_01M3DEMOTENANT0000000000",
            defaults={
                "name": "Partner Law Firm LLP",
                "deployment_mode": "D2",
                "residency_policy": "ANY",
                "idp": {"kind": "GOOGLE"},
            },
        )
        user, _ = AppUser.objects.get_or_create(
            tenant_id=tenant.tenant_id,
            email="partner.lawyer@firm.in",
            defaults={
                "user_id": "usr_01M3DEMOPARTNER000000000",
                "idp_subject": "idp_partner_demo",
                "firm_role": "PARTNER",
                "active": True,
            },
        )

    ctx = ExecutionContext(
        tenant_id=tenant.tenant_id,
        user_id=user.user_id,
        firm_role=user.firm_role,
        purpose="EXIT_CHECK_EVAL",
        residency_policy="ANY",
        dataclass="PUBLIC",
    )

    law_date = get_law_current_to_date()
    question_text = (
        "What is the scope of enquiry under Section 7 of the IBC for a financial debt and default?"
    )

    with tenant_db_context(tenant_id=ctx.tenant_id, user_id=ctx.user_id):
        query = ResearchQuery.objects.create(
            tenant_id=ctx.tenant_id,
            query_id=mint_id("qry"),
            user_id=ctx.user_id,
            text=question_text,
            mode="STANDARD",
            as_of_legal_date=law_date,
            perspective="NEUTRAL",
            stance_target="BOTH",
            request={"raw_input": question_text},
        )
        retriever = RetrievalEngine(index_family="plc_chunks")
        synthesizer = AnswerSynthesizer()

        bundle = retriever.retrieve(query=query, ctx=ctx, k=15)
        print(f"P5 Retrieval: {len(bundle.items)} items in bundle")

        t0 = time.perf_counter()
        synthesis_output, claims = synthesizer.synthesize(query=query, bundle=bundle, ctx=ctx)
        total_latency = time.perf_counter() - t0

        call_rec = (
            LLMCallRecord.objects.filter(
                tenant_id=ctx.tenant_id,
                task_id="p6.qa_synthesis@1",
            )
            .order_by("-created_at")
            .first()
        )
        assert call_rec is not None
        ep = ModelEndpoint.objects.get(endpoint_id=call_rec.endpoint_id)

        print("\n" + "=" * 80)
        print("GATEWAY MEASUREMENT: SINGLE QUESTION RUN")
        print("=" * 80)
        print(f"Endpoint ID:       {ep.endpoint_id}")
        print(f"Provider:          {ep.provider}")
        print(f"Model ID:          {ep.model_id}")
        print(f"LLMCallRecord ID:  {call_rec.call_id}")
        print(f"Gateway Latency:   {call_rec.latency_ms / 1000:.2f}s (Total: {total_latency:.2f}s)")
        print(f"Tokens In / Out:   {call_rec.tokens_in} / {call_rec.tokens_out}")
        print(f"Cost USD:          ${call_rec.usd:.6f}")
        print(f"Schema Valid:      {call_rec.schema_valid} (Repaired: {call_rec.repaired})")
        print(f"Summary:           {synthesis_output.get('summary')}")
        print(f"Claims Count:      {len(claims)}")
        for c in claims:
            print(f"  - Claim [{c.claim_id}]: {c.text}")
            print(f"    Quote:  \"{c.support[0]['quote']}\"")
            print(f"    Anchor: {c.support[0]['anchor_id']}")
        print("=" * 80)


if __name__ == "__main__":
    main()
