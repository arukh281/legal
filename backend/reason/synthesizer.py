"""Phase P6 Reasoning & Synthesis Engine — grounds Q&A answers in retrieved anchors.

Normative sources:
- docs/mvp/00_mvp_spec.md §4.1
- docs/mvp/03_data_model_and_contracts.md §3.11 (tpl.claim)
- docs/01_master_architecture.md §7.15 (Claim)
- docs/08_P6_strategic_reasoning.md §2.3
- DECISIONS.md (2026-10-10 S07 Directives):
  - Amendment #5: Never state statute content unless quoted from a retrieved anchor.
  - Amendment #6: Pass chunk text as delimited untrusted data (<source_chunk> tags).
"""

from __future__ import annotations

import logging
from typing import Any

from anchor_lib.ids import mint_id
from gateway.runner import run as gateway_run
from reason.models import Claim
from retrieve.models import EvidenceBundle, ResearchQuery
from workspace.authz import ExecutionContext

logger = logging.getLogger(__name__)

QA_SYNTHESIS_TASK_ID = "p6.qa_synthesis@1"


class AnswerSynthesizer:
    """Answer Synthesizer calling Model Gateway with strictly delimited chunk data."""

    def synthesize(
        self,
        query: ResearchQuery,
        bundle: EvidenceBundle,
        ctx: ExecutionContext,
    ) -> tuple[dict[str, Any], list[Claim]]:
        """Synthesize answer from EvidenceBundle or report out-of-corpus honestly."""
        # 1. Honest out-of-corpus gate (Non-negotiable #3)
        if not bundle.items:
            payload = {
                "summary": "The requested topic was not found in the MVP corpus. Out of corpus means 'not in MVP corpus', not that the legal proposition is incorrect.",
                "in_corpus": False,
                "claims": [],
                "contrary_sweep": {
                    "status": "NOT_IN_CORPUS",
                    "notes": "No matching authorities found in MVP corpus.",
                },
            }
            return payload, []

        # 2. Format delimited untrusted chunk data blocks (Amendment #6)
        evidence_chunks: list[dict[str, Any]] = []
        for item in bundle.items:
            ctx_data = item.get("context", {})
            evidence_chunks.append(
                {
                    "item_id": item["item_id"],
                    "anchor_id": item["anchor_ids"][0],
                    "work_id": item.get("work_id") or "UNKNOWN",
                    "court_id": ctx_data.get("court_id"),
                    "title": ctx_data.get("header"),
                    "text": item.get("excerpt", ""),
                }
            )

        # 3. Model Gateway inputs
        gateway_inputs = {
            "question": query.text,
            "as_of_legal_date": query.as_of_legal_date.isoformat(),
            "evidence_chunks": evidence_chunks,
        }

        # 4. Invoke Model Gateway
        result = gateway_run(
            task_id=QA_SYNTHESIS_TASK_ID,
            inputs=gateway_inputs,
            ctx=ctx,
            pipeline_version="p6.reasoner@0.1.0|qa_synthesis_v1",
        )
        output = result.output

        # 5. Mint Claim instances for valid in-corpus claims
        claims: list[Claim] = []
        if output.get("in_corpus", True):
            for c_dict in output.get("claims", []):
                claim_id = mint_id("clm")
                claim = Claim(
                    tenant_id=ctx.tenant_id,
                    claim_id=claim_id,
                    owner_kind="ANSWER",
                    owner_id=query.query_id,
                    section="answer",
                    text=c_dict["text"],
                    claim_type=c_dict.get("claim_type", "LEGAL_PROPOSITION"),
                    support=[
                        {
                            "anchor_id": c_dict["anchor_id"],
                            "quote": c_dict["quote"],
                            "span": [0, len(c_dict["quote"])],
                            "support_type": c_dict.get("support_type", "DIRECT"),
                        }
                    ],
                    contrary=[],
                    confidence=1.0,
                    depends_on_claim_ids=[],
                    issue_ids=[f"{query.query_id}/i1"],
                )
                claim.save()
                claims.append(claim)

        return output, claims
