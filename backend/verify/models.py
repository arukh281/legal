"""Domain models for Phase P8 Verification (tpl schema).

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.12 (tpl.verification_report, tpl.claim_verification)
- docs/01_master_architecture.md §7.19 (VerificationReport)
- docs/10_P8_verification_evaluation.md §5.3, §5.4 (Warrant ladder C0-C10)
- docs/01a_spine_decision_record.md: D9, D12 (vr_ prefix)
- DECISIONS.md (2026-10-10: S07 Directives)
"""

from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.fields.composite import CompositePrimaryKey
from django.utils import timezone

from anchor_lib.models import DomainModel, PrefixedULIDField
from ops.models import PipelineVersion


class VerificationReport(DomainModel):
    """Integrity and grounding verification report for answers, memos, or drafts (tpl.verification_report)."""

    pk = CompositePrimaryKey("tenant_id", "report_id")
    tenant_id = models.TextField()
    report_id = PrefixedULIDField(prefix="vr")
    request_id = models.TextField()
    subject = models.JSONField()
    as_of_legal_date = models.DateField()
    as_known_at = models.DateTimeField(default=timezone.now)
    graph_watermark = models.BigIntegerField(default=0)
    anchor_generation = models.TextField()
    verifier_version = models.ForeignKey(
        PipelineVersion,
        on_delete=models.PROTECT,
        db_column="verifier_version",
    )
    gate = models.TextField(
        choices=[("PASS", "PASS"), ("PARTIAL", "PARTIAL"), ("BLOCK", "BLOCK")]
    )
    section_gates = models.JSONField(null=True, blank=True)
    gate_reasons: list[str] = ArrayField(models.TextField(), default=list)  # type: ignore[assignment]
    withheld_claim_ids: list[str] = ArrayField(models.TextField(), default=list)  # type: ignore[assignment]
    withheld_sections: list[str] = ArrayField(models.TextField(), default=list)  # type: ignore[assignment]
    coverage = models.JSONField(default=dict)
    degradations = models.JSONField(default=list)
    calibration_state = models.TextField(default="UNCALIBRATED_PREVIEW")
    context_warnings: list[str] = ArrayField(models.TextField(), null=True, blank=True)  # type: ignore[assignment]
    supersedes_report_id = models.TextField(null=True, blank=True)
    signature = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'tpl"."verification_report'

    def __str__(self) -> str:
        return f"VerificationReport({self.report_id}: gate={self.gate})"


class ClaimVerification(DomainModel):
    """Detailed verification verdict per claim (tpl.claim_verification)."""

    pk = CompositePrimaryKey("tenant_id", "report_id", "claim_id")
    tenant_id = models.TextField()
    report_id = models.TextField()
    claim_id = models.TextField()
    claim_hash = models.TextField()
    status = models.TextField(
        choices=[
            ("VERIFIED", "VERIFIED"),
            ("PARTIAL", "PARTIAL"),
            ("UNSUPPORTED", "UNSUPPORTED"),
            ("CONTRADICTED", "CONTRADICTED"),
            ("BAD_LAW", "BAD_LAW"),
            ("UNVERIFIABLE", "UNVERIFIABLE"),
        ]
    )
    display_band = models.TextField(
        choices=[
            ("VERIFIED", "VERIFIED"),
            ("VERIFIED_WITH_CAVEAT", "VERIFIED_WITH_CAVEAT"),
            ("CHECK", "CHECK"),
            ("WITHHELD", "WITHHELD"),
        ]
    )
    calibrated_confidence = models.FloatField(null=True, blank=True)
    confidence_stratum = models.TextField(default="UNCALIBRATED_PREVIEW")
    warrant = models.JSONField()
    checks = models.JSONField(default=list)
    reason_codes: list[str] = ArrayField(models.TextField(), default=list)  # type: ignore[assignment]
    narrowed_text = models.TextField(null=True, blank=True)
    suggested_anchor_ids: list[str] = ArrayField(models.TextField(), null=True, blank=True)  # type: ignore[assignment]
    authority_snapshot = models.JSONField(null=True, blank=True)
    human_review = models.JSONField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'tpl"."claim_verification'

    def __str__(self) -> str:
        return f"ClaimVerification({self.claim_id}: {self.status} / {self.display_band})"
