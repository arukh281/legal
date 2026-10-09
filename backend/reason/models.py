"""Domain models for Phase P6 Strategic Reasoning & Claims (tpl schema).

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.11 (tpl.claim)
- docs/01_master_architecture.md §7.15 (Claim)
- docs/01a_spine_decision_record.md: D9, D12 (clm_ prefix)
- DECISIONS.md (2026-10-10: S07 Directives)
"""

from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.fields.composite import CompositePrimaryKey

from anchor_lib.models import DomainModel, PrefixedULIDField


class Claim(DomainModel):
    """A factual, legal, procedural, or strategic claim pinned to anchors (tpl.claim)."""

    pk = CompositePrimaryKey("tenant_id", "claim_id")
    tenant_id = models.TextField()
    claim_id = PrefixedULIDField(prefix="clm")
    owner_kind = models.TextField(
        choices=[("MEMO", "MEMO"), ("ANSWER", "ANSWER"), ("DRAFT", "DRAFT")]
    )
    owner_id = models.TextField()
    section = models.TextField(null=True, blank=True)
    text = models.TextField()
    claim_type = models.TextField(
        choices=[
            ("LEGAL_PROPOSITION", "LEGAL_PROPOSITION"),
            ("RECORD_FACT", "RECORD_FACT"),
            ("PROCEDURAL", "PROCEDURAL"),
            ("STRATEGIC_OPINION", "STRATEGIC_OPINION"),
        ]
    )
    support = models.JSONField(default=list)
    contrary = models.JSONField(default=list)
    confidence = models.FloatField(null=True, blank=True)
    depends_on_claim_ids: list[str] = ArrayField(models.TextField(), default=list)  # type: ignore[assignment]
    issue_ids: list[str] = ArrayField(models.TextField(), default=list)  # type: ignore[assignment]
    origin_role = models.TextField(null=True, blank=True)
    revision_of = models.TextField(null=True, blank=True)
    strength = models.TextField(null=True, blank=True)
    assumptions: list[str] = ArrayField(models.TextField(), null=True, blank=True)  # type: ignore[assignment]

    class Meta:
        managed = False
        db_table = 'tpl"."claim'

    def __str__(self) -> str:
        return f"Claim({self.claim_id}: {self.text[:40]})"
