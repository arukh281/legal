"""Evaluation Runner: Session S07 Weekly Exit Check (Demo 1).

Executes the 3 confirmed IBC questions + 1 out-of-corpus question end-to-end through
the research engine (P5 retrieval -> P6 synthesis -> P8 verification), demonstrating
honest groundings, claim-level pinpoints, uncalibrated preview bands, and contrary sweep.

Normative sources:
- docs/mvp/00_mvp_spec.md §4.1
- docs/mvp/05_build_plan.md §4 (Week 4 Exit Check)
- DECISIONS.md (2026-10-10 S07 Directives)
"""

# ruff: noqa: E402

from __future__ import annotations

import os
import sys
from pathlib import Path

import django

# Setup Django environment
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.local")
django.setup()

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from parse.models import Anchor
from reason.synthesizer import AnswerSynthesizer
from retrieve.models import ResearchQuery
from retrieve.retriever import RetrievalEngine, get_law_current_to_date
from verify.models import ClaimVerification
from verify.verifier import VerificationEngine
from workspace.authz import ExecutionContext
from workspace.db import tenant_db_context
from workspace.models import AppUser, Tenant

DEMO_QUESTIONS = [
    {
        "id": "Q1_SECTION_7",
        "question": "What is the scope of enquiry under Section 7 of the IBC for a financial debt and default?",
        "topic": "Section 7 IBC: Scope of enquiry on financial debt and default",
        "expected_in_corpus": True,
    },
    {
        "id": "Q2_SECTION_9_10A",
        "question": "Can an operational creditor invoke Section 9 for default during the Section 10A period?",
        "topic": "Section 9 & 10A IBC: Bar on operational creditor applications during COVID excluded period",
        "expected_in_corpus": True,
    },
    {
        "id": "Q3_SECTION_14_NI",
        "question": "Does moratorium under Section 14 of IBC apply to Section 138 NI Act proceedings?",
        "topic": "Section 14 IBC: Scope of moratorium qua Section 138 Negotiable Instruments Act",
        "expected_in_corpus": True,
    },
    {
        "id": "Q4_OUT_OF_CORPUS",
        "question": "What are the rules for maritime salvage under the Admiralty Act 2017?",
        "topic": "Admiralty Act 2017 (Out of MVP Corpus - Honest Negative Test)",
        "expected_in_corpus": False,
    },
]


def run_exit_check() -> int:
    print("=" * 80)
    print("SESSION S07 EXIT CHECK DEMO: RESEARCH Q&A WITH PINPOINTED CLAIMS")
    print("=" * 80)

    # 1. Ensure test tenant & user
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
    )

    law_date = get_law_current_to_date()
    print(f"[*] Tenant: {tenant.tenant_id} ({tenant.name})")
    print(f"[*] Actor: {user.email} (Role: {user.firm_role})")
    print(f"[*] Law current to: {law_date.isoformat()} (dynamically derived from plc.capture)")
    print("-" * 80)

    results = []
    failures = 0

    retriever = RetrievalEngine(index_family="plc_chunks")
    synthesizer = AnswerSynthesizer()
    verifier = VerificationEngine()

    for idx, q_spec in enumerate(DEMO_QUESTIONS, start=1):
        q_id = str(q_spec["id"])
        question_text = str(q_spec["question"])
        print(f"\n[DEMO RUN #{idx}] {q_id}")
        print(f"Question: \"{question_text}\"")

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

            # Phase P5: Retrieval
            bundle = retriever.retrieve(query=query, ctx=ctx, k=15)
            print(f"  -> P5 Retrieval: {len(bundle.items)} evidence chunks retrieved (bundle_id: {bundle.bundle_id})")

            # Phase P6: Synthesis
            synthesis_output, claims = synthesizer.synthesize(query=query, bundle=bundle, ctx=ctx)
            print(f"  -> P6 Synthesis: in_corpus={synthesis_output.get('in_corpus')}, claims_count={len(claims)}")

            # Phase P8: Verification
            report = verifier.verify(query_id=query.query_id, claims=claims, bundle=bundle, ctx=ctx)
            print(f"  -> P8 Verification: gate={report.gate}, withheld={len(report.withheld_claim_ids)}")

            # Format claims
            verifications = ClaimVerification.objects.filter(
                tenant_id=ctx.tenant_id, report_id=report.report_id
            )
            ver_by_claim_id = {v.claim_id: v for v in verifications}

            # Validations per S07 Directives
            if q_spec["expected_in_corpus"]:
                if not synthesis_output.get("in_corpus"):
                    print("  [FAIL] Expected in-corpus hits but got out-of-corpus.")
                    failures += 1
                if len(claims) == 0:
                    print("  [FAIL] Expected grounded claims but got 0.")
                    failures += 1

                for c in claims:
                    v_info = ver_by_claim_id.get(c.claim_id)
                    assert v_info is not None
                    # Amendment #1: Display band must be 'quote verified · uncalibrated preview'
                    display_band = (
                        "quote verified · uncalibrated preview"
                        if v_info.display_band == "VERIFIED"
                        else v_info.display_band
                    )
                    print(f"    Claim [{c.claim_id}]: {c.text[:70]}...")
                    print(f"      Status: {v_info.status} | Band: \"{display_band}\"")
                    print(f"      Anchor: {c.support[0]['anchor_id']}")
                    print(f"      Quote:  \"{c.support[0]['quote'][:80]}...\"")

                    # Verify anchor exists in corpus
                    anchor_row = Anchor.objects.filter(anchor_id=c.support[0]["anchor_id"]).first()
                    if anchor_row:
                        print(f"      Corpus Check: ✓ Exists in plc.anchor (Work: {anchor_row.work_id})")
                    else:
                        print("      Corpus Check: ✗ Anchor not found in database!")
                        failures += 1
            else:
                # Out of corpus check
                if synthesis_output.get("in_corpus") is not False:
                    print("  [FAIL] Expected out_of_corpus=False for Admiralty question.")
                    failures += 1
                if len(claims) != 0:
                    print("  [FAIL] Expected 0 claims for out-of-corpus question.")
                    failures += 1
                summary_text = str(synthesis_output.get("summary") or "")
                print(f"    Honest Negative Output: \"{summary_text[:100]}...\"")
                print("    Claims minted: 0 (Honest zero-hallucination compliance)")

            # Check Contrary Sweep status LIMITED
            contrary_sweep = bundle.coverage["per_issue"]["main"]["adverse_search"]
            assert contrary_sweep["status"] == "LIMITED", f"Unexpected status {contrary_sweep['status']}"
            assert contrary_sweep["reason"] == "lexical only, no citator"
            print(f"  -> Contrary Sweep: STATUS={contrary_sweep['status']} ({contrary_sweep['reason']})")

            results.append({
                "q_id": q_id,
                "in_corpus": synthesis_output.get("in_corpus"),
                "claims": len(claims),
                "gate": report.gate,
            })

    print("\n" + "=" * 80)
    print("EXIT CHECK SUMMARY SCORECARD")
    print("=" * 80)
    for r in results:
        print(f"  - {r['q_id']}: in_corpus={r['in_corpus']}, claims={r['claims']}, gate={r['gate']}")

    if failures == 0:
        print("\n>>> ALL S07 DEMO EXIT CHECKS PASSED WITH ZERO TOLERANCE GATES MET! <<<")
        return 0
    else:
        print(f"\n>>> EXIT CHECKS FAILED: {failures} ERRORS ENCOUNTERED <<<")
        return 1


if __name__ == "__main__":
    sys.exit(run_exit_check())
