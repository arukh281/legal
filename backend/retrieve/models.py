"""Domain models for Phase P5 Retrieval (tpl schema).

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.11 (tpl.research_query, tpl.evidence_bundle)
- docs/01_master_architecture.md §7.8 (ResearchQuery), §7.9 (EvidenceBundle)
- docs/01a_spine_decision_record.md: D9, D12 (qry_, evb_ prefixes)
- DECISIONS.md (2026-10-10: S07 Directives)
"""

from __future__ import annotations

from django.db import models
from django.db.models.fields.composite import CompositePrimaryKey
from django.utils import timezone

from anchor_lib.models import DomainModel, PrefixedULIDField
from ops.models import PipelineVersion


class ResearchQuery(DomainModel):
    """A research query initiated by a lawyer or agent (tpl.research_query)."""

    pk = CompositePrimaryKey("tenant_id", "query_id")
    tenant_id = models.TextField()
    query_id = PrefixedULIDField(prefix="qry")
    matter_id = models.TextField(null=True, blank=True)
    user_id = models.TextField()
    text = models.TextField()
    mode = models.TextField(
        choices=[("QUICK", "QUICK"), ("STANDARD", "STANDARD"), ("DEEP", "DEEP")],
        default="STANDARD",
    )
    as_of_legal_date = models.DateField()
    as_known_at = models.DateTimeField(default=timezone.now)
    forum = models.JSONField(null=True, blank=True)
    perspective = models.TextField(default="NEUTRAL")
    stance_target = models.TextField(default="BOTH")
    request = models.JSONField(default=dict)
    answer = models.JSONField(null=True, blank=True)
    verification_report_id = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'tpl"."research_query'

    def __str__(self) -> str:
        return f"ResearchQuery({self.query_id}: {self.text[:40]})"


class EvidenceBundle(DomainModel):
    """Legally weighted evidence bundle compiled for a research query (tpl.evidence_bundle)."""

    pk = CompositePrimaryKey("tenant_id", "bundle_id")
    tenant_id = models.TextField()
    bundle_id = PrefixedULIDField(prefix="evb")
    query_id = models.TextField()
    as_of_legal_date = models.DateField()
    as_known_at = models.DateTimeField(default=timezone.now)
    index_generation = models.TextField()
    graph_watermark = models.BigIntegerField(default=0)
    pipeline_version = models.ForeignKey(
        PipelineVersion,
        on_delete=models.PROTECT,
        db_column="pipeline_version",
    )
    issues = models.JSONField(default=list)
    items = models.JSONField(default=list)
    coverage = models.JSONField(default=dict)
    warnings = models.JSONField(default=list)
    searched = models.JSONField(default=list)
    trace_id = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'tpl"."evidence_bundle'

    def __str__(self) -> str:
        return f"EvidenceBundle({self.bundle_id} for {self.query_id})"
