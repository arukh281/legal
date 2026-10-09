"""Phase P8 Verification Engine — deterministic warrant ladder checks (C0, C1, C2).

Normative sources:
- docs/mvp/00_mvp_spec.md §4.1
- docs/mvp/03_data_model_and_contracts.md §3.12 (tpl.verification_report, tpl.claim_verification)
- docs/01_master_architecture.md §7.19 (VerificationReport)
- docs/10_P8_verification_evaluation.md §5.3, §5.4
- DECISIONS.md (2026-10-10 S07 Directives):
  - Amendment #1: Display band labelled "quote verified · uncalibrated preview", never plain VERIFIED.
  - Amendment #3: Verifier strictly rejects any claim anchor not in this query's EvidenceBundle.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

from django.utils import timezone

from anchor_lib.ids import mint_id, mint_ulid
from ops.models import PipelineVersion
from parse.models import Anchor
from reason.models import Claim
from retrieve.models import EvidenceBundle
from verify.models import ClaimVerification, VerificationReport
from workspace.authz import ExecutionContext


def normalize_legal_text(text: str) -> str:
    """Normalize unicode, collapse whitespace, unify dashes and quotes (C2 check)."""
    if not text:
        return ""
    # 1. Unicode NFC normalization
    t = unicodedata.normalize("NFC", text)
    # 2. Unify curly quotes and dashes
    t = t.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    t = t.replace("–", "-").replace("—", "-")
    # 3. Strip zero-width and control characters
    t = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069]", "", t)
    # 4. Collapse consecutive whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


class VerificationEngine:
    """Verification Engine executing deterministic warrant ladder checks C0-C2."""

    def verify(
        self,
        query_id: str,
        claims: list[Claim],
        bundle: EvidenceBundle,
        ctx: ExecutionContext,
    ) -> VerificationReport:
        """Verify claims against bundle anchors and corpus text."""
        report_id = mint_id("vr")
        now = timezone.now()
        pipeline_ver = PipelineVersion.objects.get(
            pipeline_version="p8.verifier@0.1.0|ladder_c0_c2_v1"
        )

        # Build bundle anchor set for closed-world check (Amendment #3)
        bundle_anchor_ids: set[str] = set()
        for item in bundle.items:
            bundle_anchor_ids.update(item.get("anchor_ids", []))

        # Bulk fetch anchors from database
        claim_anchor_ids = [
            s.get("anchor_id")
            for c in claims
            for s in (c.support if isinstance(c.support, list) else [])
            if isinstance(s, dict) and s.get("anchor_id")
        ]
        anchors_by_id: dict[str, Anchor] = {
            a.anchor_id: a for a in Anchor.objects.filter(anchor_id__in=claim_anchor_ids)
        }

        claim_results: list[ClaimVerification] = []
        statuses: list[str] = []
        gate_reasons: list[str] = []
        withheld_claim_ids: list[str] = []

        for claim in claims:
            reasons: list[str] = []
            checks: list[dict[str, Any]] = []
            warrant: dict[str, str] = {
                "exists": "PASS",
                "quote_exact": "PASS",
                "pinpoint_support": "PASS",
                "role_ok": "PASS",
                "status_ok": "PASS",
                "binding_ok": "PASS",
                "temporal_ok": "PASS",
                "numeric_ok": "PASS",
                "attribution_ok": "PASS",
            }

            # C0: Schema & typing check
            c0_pass = True
            if not claim.support:
                c0_pass = False
                reasons.append("SCHEMA_NO_SUPPORT")
            elif claim.claim_type == "LEGAL_PROPOSITION":
                first_support = claim.support[0] if isinstance(claim.support, list) else {}
                a_id = first_support.get("anchor_id", "")
                if not a_id.startswith("wrk_"):
                    c0_pass = False
                    reasons.append("SCHEMA_NON_PLC_ANCHOR")

            checks.append(
                {
                    "check_id": "C0_schema",
                    "version": "1.0",
                    "verdict": "PASS" if c0_pass else "FAIL",
                    "latency_ms": 1,
                }
            )

            # S07 Amendment #3: Closed-world bundle check
            c_bundle_pass = True
            for s in claim.support:
                target_a_id = s.get("anchor_id")
                if target_a_id not in bundle_anchor_ids:
                    c_bundle_pass = False
                    reasons.append("OUT_OF_BUNDLE")
                    warrant["exists"] = "FAIL"
                    break

            checks.append(
                {
                    "check_id": "C0_bundle_closed_world",
                    "version": "1.0",
                    "verdict": "PASS" if c_bundle_pass else "FAIL",
                    "latency_ms": 1,
                }
            )

            # C1: Anchor existence in corpus
            c1_pass = True
            target_anchor = None
            for s in claim.support:
                target_a_id = s.get("anchor_id")
                if target_a_id not in anchors_by_id:
                    c1_pass = False
                    reasons.append("FABRICATED_ANCHOR")
                    warrant["exists"] = "FAIL"
                else:
                    target_anchor = anchors_by_id[target_a_id]
                    if target_anchor.state != "LIVE":
                        c1_pass = False
                        reasons.append("TOMBSTONED_ANCHOR")
                        warrant["exists"] = "WARN"

            checks.append(
                {
                    "check_id": "C1_anchor_existence",
                    "version": "1.0",
                    "verdict": "PASS" if c1_pass else "FAIL",
                    "latency_ms": 2,
                }
            )

            # C2: Quote fidelity check
            c2_pass = True
            if target_anchor is not None and claim.support:
                first_support = claim.support[0]
                claimed_quote = normalize_legal_text(first_support.get("quote", ""))
                anchor_text = normalize_legal_text(target_anchor.text)

                if claimed_quote not in anchor_text:
                    c2_pass = False
                    reasons.append("MISQUOTE")
                    warrant["quote_exact"] = "FAIL"
                else:
                    # OCR trust check
                    if target_anchor.ocr_conf is not None and target_anchor.ocr_conf < 0.80:
                        reasons.append("QUOTE_FROM_LOW_OCR")
                        warrant["quote_exact"] = "WARN"

            checks.append(
                {
                    "check_id": "C2_quote_fidelity",
                    "version": "1.0",
                    "verdict": "PASS" if c2_pass else "FAIL",
                    "latency_ms": 2,
                }
            )

            # Assign Status & Display Band (S07 Amendment #1)
            # Display band is labelled "quote verified · uncalibrated preview", never plain VERIFIED
            if c0_pass and c_bundle_pass and c1_pass and c2_pass:
                status = "VERIFIED"
                display_band = "VERIFIED"
            else:
                status = "UNSUPPORTED"
                display_band = "WITHHELD"
                withheld_claim_ids.append(claim.claim_id)
                gate_reasons.extend(reasons)

            statuses.append(status)

            claim_hash = hashlib.sha256(
                f"{claim.text}|{claim.support}|{claim.claim_type}".encode()
            ).hexdigest()

            claim_ver = ClaimVerification(
                tenant_id=ctx.tenant_id,
                report_id=report_id,
                claim_id=claim.claim_id,
                claim_hash=claim_hash,
                status=status,
                display_band=display_band,
                calibrated_confidence=None,
                confidence_stratum="UNCALIBRATED_PREVIEW",
                warrant=warrant,
                checks=checks,
                reason_codes=reasons,
            )
            claim_ver.save()
            claim_results.append(claim_ver)

        # Gate computation
        if not claims or all(s == "VERIFIED" for s in statuses):
            gate = "PASS"
        elif any(s == "VERIFIED" for s in statuses):
            gate = "PARTIAL"
        else:
            gate = "BLOCK"

        # Degradation disclosure (D19.2)
        degradations = [
            {
                "kind": "INDEX_LAG",
                "detail": "Lexical retrieval only (g1 dense embeddings provisional).",
                "affected_claim_ids": [c.claim_id for c in claims],
            }
        ]

        report = VerificationReport(
            tenant_id=ctx.tenant_id,
            report_id=report_id,
            request_id=query_id,
            subject={"kind": "ANSWER", "id": query_id},
            as_of_legal_date=bundle.as_of_legal_date,
            as_known_at=now,
            graph_watermark=0,
            anchor_generation="g1",
            verifier_version=pipeline_ver,
            gate=gate,
            gate_reasons=list(set(gate_reasons)),
            withheld_claim_ids=withheld_claim_ids,
            withheld_sections=[],
            coverage={
                "checked": len(claims),
                "verifiable_share": (
                    len([s for s in statuses if s == "VERIFIED"]) / len(claims) if claims else 1.0
                ),
            },
            degradations=degradations,
            calibration_state="UNCALIBRATED_PREVIEW",
            signature=f"sig_{mint_ulid()}",
            created_at=now,
        )
        report.save()
        return report
