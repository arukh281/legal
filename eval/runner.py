"""Evaluation Suite Runner executing gold cases through the research pipeline.

Normative sources:
- docs/mvp/06_test_set_plan.md §6, §7
- docs/mvp/03_data_model_and_contracts.md §3.15
- Session S08 Amendments 2(a)–2(d)
"""

from __future__ import annotations

import logging
from typing import Any

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from django.db import transaction
from gateway.models import ModelEndpoint
from ops.models import EvalCase, EvalResult, EvalRun, GoldSet, PipelineVersion
from reason.synthesizer import AnswerSynthesizer
from retrieve.models import ResearchQuery
from retrieve.retriever import RetrievalEngine, get_law_current_to_date
from verify.verifier import VerificationEngine
from workspace.authz import ExecutionContext
from workspace.db import tenant_db_context
from workspace.models import AppUser, Tenant

from eval.evaluator import DeterministicEvaluator
from eval.scorecard import generate_markdown_scorecard

logger = logging.getLogger(__name__)


class EvalRunner:
    """Executes evaluation cases and records audited results."""

    def __init__(self) -> None:
        self.retriever = RetrievalEngine(index_family="plc_chunks")
        self.synthesizer = AnswerSynthesizer()
        self.verifier = VerificationEngine()
        self.evaluator = DeterministicEvaluator()

    def run_suite(
        self,
        gold_set_id: str,
        split: str | None = None,
        specific_case_id: str | None = None,
        ctx: ExecutionContext | None = None,
        dry_run: bool = False,
    ) -> tuple[EvalRun, list[dict[str, Any]], str]:
        """Execute gold cases in the given suite, score results, and record an EvalRun."""
        with admin_db_context():
            gold_set = GoldSet.objects.get(gold_set_id=gold_set_id)
            case_qs = EvalCase.objects.filter(gold_set=gold_set, stale=False)
            if split:
                case_qs = case_qs.filter(split=split)
            if specific_case_id:
                case_qs = case_qs.filter(eval_case_id=specific_case_id)

            cases = list(case_qs.order_by("eval_case_id"))
            if not cases:
                raise ValueError(f"No active eval cases found for suite {gold_set_id}")

        # Set up execution context
        if ctx is None:
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
                user_id=user.user_id,
                tenant_id=tenant.tenant_id,
                firm_role=user.firm_role,
                residency_policy="ANY",
                purpose="EXIT_CHECK_EVAL",
                dataclass="PUBLIC",
            )

        run_id = mint_id("evr")
        law_date = get_law_current_to_date()
        case_summaries: list[dict[str, Any]] = []
        zero_tolerance_totals = {
            "fabricated_anchors": 0,
            "unmapped_tombstones": 0,
            "ungrounded_claims": 0,
            "sentinel_leaks": 0,
        }
        reviewed_zero_tolerance = {
            "fabricated_anchors": 0,
            "unmapped_tombstones": 0,
            "ungrounded_claims": 0,
            "sentinel_leaks": 0,
        }
        total_prop_scores: list[float] = []
        passed_cases = 0
        eval_results_to_create: list[dict[str, Any]] = []
        case_models: dict[str, dict[str, Any]] = {}

        # Execute each case within tenant context
        for c in cases:
            question_text = c.input.get("question", "")
            raw_law_date = c.input.get("as_of_legal_date")
            if isinstance(raw_law_date, str):
                import datetime
                case_law_date = datetime.date.fromisoformat(raw_law_date)
            elif raw_law_date:
                case_law_date = raw_law_date
            else:
                case_law_date = law_date

            with tenant_db_context(tenant_id=ctx.tenant_id, user_id=ctx.user_id):
                query = ResearchQuery.objects.create(
                    tenant_id=ctx.tenant_id,
                    query_id=mint_id("qry"),
                    user_id=ctx.user_id,
                    text=question_text,
                    mode="STANDARD",
                    as_of_legal_date=case_law_date,
                    perspective="NEUTRAL",
                    stance_target="BOTH",
                    request={"raw_input": question_text, "eval_case_id": c.eval_case_id},
                )

                # 1. Retrieve
                bundle = self.retriever.retrieve(query=query, ctx=ctx, k=15)
                # 2. Synthesize
                synthesis_output, claims = self.synthesizer.synthesize(
                    query=query, bundle=bundle, ctx=ctx
                )
                # 3. Verify
                v_report = self.verifier.verify(
                    query_id=query.query_id, claims=claims, bundle=bundle, ctx=ctx
                )

            # 4. Deterministic Evaluation
            c_eval = self.evaluator.evaluate(
                case_id=c.eval_case_id,
                expected=c.expected,
                actual_output=synthesis_output,
                actual_claims=claims,
                verification_report=v_report,
            )

            is_reviewed = (c.provenance.get("source") != "SYNTHETIC") or (c.provenance.get("reviewed") is True)

            for k in zero_tolerance_totals:
                val = c_eval.gate_checks.get(k, 0)
                zero_tolerance_totals[k] += val
                if is_reviewed:
                    reviewed_zero_tolerance[k] += val

            if c_eval.passed:
                passed_cases += 1
            total_prop_scores.append(c_eval.score)

            eval_results_to_create.append(
                {
                    "result_id": mint_id("evres"),
                    "eval_case": c,
                    "actual": {
                        "in_corpus": synthesis_output.get("in_corpus"),
                        "summary": synthesis_output.get("summary"),
                        "claims_count": len(claims),
                        "claims": [
                            {"id": cl.claim_id, "text": cl.text, "support": cl.support}
                            for cl in claims
                        ],
                    },
                    "passed": c_eval.passed,
                    "score": c_eval.score,
                    "reasons": c_eval.reasons,
                    "gate_checks": c_eval.gate_checks,
                }
            )

            call_rec = getattr(self.synthesizer, "last_call_record", None)
            if call_rec:
                ep_id = call_rec.endpoint_id
                with admin_db_context():
                    ep_obj = ModelEndpoint.objects.filter(endpoint_id=ep_id).first()
                actual_model = ep_obj.model_id if ep_obj else ep_id
                ep_provider = ep_obj.provider if ep_obj else "unknown"
            else:
                ep_id = "N/A"
                actual_model = "out_of_corpus"
                ep_provider = None

            case_models[c.eval_case_id] = {
                "endpoint_id": ep_id,
                "model": actual_model,
                "provider": ep_provider,
                "call_id": call_rec.call_id if call_rec else None,
            }

            case_summaries.append(
                {
                    "eval_case_id": c.eval_case_id,
                    "split": c.split,
                    "task": c.task,
                    "endpoint_id": ep_id,
                    "model": actual_model,
                    "passed": c_eval.passed,
                    "score": c_eval.score,
                    "reasons": c_eval.reasons,
                    "gate_checks": c_eval.gate_checks,
                    "in_corpus_match": c_eval.in_corpus_match,
                    "provenance": c.provenance,
                    "is_reviewed": is_reviewed,
                }
            )

        n_total = len(cases)
        reviewed_cases_count = sum(1 for cs in case_summaries if cs["is_reviewed"])
        synthetic_unreviewed_count = n_total - reviewed_cases_count

        has_any_zt_failure = any(v > 0 for v in zero_tolerance_totals.values())

        # Gate Decision Rule (Amendments 2b, 2c):
        # - Any zero-tolerance failure fails the run -> REJECT
        # - Below n=30: PREVIEW (no statistical PROMOTE/REJECT)
        # - Unreviewed synthetic cases excluded from promotion gate
        if has_any_zt_failure:
            gate_decision = "REJECT"
        elif reviewed_cases_count < 30:
            gate_decision = "PREVIEW"
        else:
            gate_decision = "PROMOTE"

        avg_recall = sum(total_prop_scores) / n_total if n_total > 0 else 0.0

        active_providers = {
            cm["provider"] for cm in case_models.values() if cm["provider"] is not None
        }
        overall_adapter = "fake" if "fake" in active_providers else "real"
        unique_endpoints = sorted(
            {cm["endpoint_id"] for cm in case_models.values() if cm["endpoint_id"] != "N/A"}
        )
        unique_models = sorted(
            {cm["model"] for cm in case_models.values() if cm["model"] != "out_of_corpus"}
        )

        pipeline_ver = PipelineVersion.objects.first()
        candidate_info = {
            "pipeline_version": pipeline_ver.pipeline_version if pipeline_ver else "dev",
            "task": cases[0].task if cases else "p6.qa_synthesis@1",
            "adapter": overall_adapter,
            "endpoints": unique_endpoints,
            "models": unique_models,
            "cases": case_models,
        }
        if len(unique_endpoints) == 1:
            candidate_info["endpoint_id"] = unique_endpoints[0]
        if len(unique_models) == 1:
            candidate_info["model"] = unique_models[0]

        metrics_info = {
            "n": n_total,
            "n_reviewed": reviewed_cases_count,
            "n_synthetic_unreviewed": synthetic_unreviewed_count,
            "passed_cases": passed_cases,
            "avg_proposition_recall": avg_recall,
            "zero_tolerance": zero_tolerance_totals,
            "zero_tolerance_reviewed": reviewed_zero_tolerance,
        }

        with admin_db_context(), transaction.atomic(using="owner"):
            eval_run = EvalRun(
                run_id=run_id,
                gold_set=gold_set,
                candidate=candidate_info,
                metrics=metrics_info,
                gate_decision=gate_decision,
                sentinel_failures=None,
                cost_usd=None,
            )
            if not dry_run:
                eval_run.save()
                for r_data in eval_results_to_create:
                    EvalResult.objects.create(
                        result_id=r_data["result_id"],
                        run=eval_run,
                        eval_case=r_data["eval_case"],
                        actual=r_data["actual"],
                        passed=r_data["passed"],
                        score=r_data["score"],
                        reasons=r_data["reasons"],
                        gate_checks=r_data["gate_checks"],
                    )
            else:
                transaction.set_rollback(True, using="owner")

        scorecard_md = generate_markdown_scorecard(eval_run, case_summaries)
        return eval_run, case_summaries, scorecard_md
