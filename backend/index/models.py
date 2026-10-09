"""Django domain models for indexing, representations, and generation lifecycle.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.5
- docs/04_P2_enrichment_indexing.md §2.2, §2.3, §2.7
- docs/01_master_architecture.md §7.2, §7.3, §7.4
"""

from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.fields.composite import CompositePrimaryKey
from django.utils import timezone


class IndexGeneration(models.Model):
    """Immutable, versioned projection of anchors into retrieval units (ops.index_generation)."""

    pk = CompositePrimaryKey("index_family", "generation")
    index_family = models.TextField()
    generation = models.TextField()
    chunker_version = models.TextField()
    embed_model = models.TextField()
    embed_dims = models.IntegerField()
    fts_config = models.TextField()
    state = models.TextField(
        choices=[
            ("BUILDING", "BUILDING"),
            ("SHADOW", "SHADOW"),
            ("LIVE", "LIVE"),
            ("RETIRED", "RETIRED"),
            ("ROLLED_BACK", "ROLLED_BACK"),
        ]
    )
    eval_report_uri = models.TextField(null=True, blank=True)
    gate_decision_id = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    promoted_at = models.DateTimeField(null=True, blank=True)
    rollback_deadline = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'ops"."index_generation'

    def __str__(self) -> str:
        return f"{self.index_family}:{self.generation} ({self.state})"


class IndexAlias(models.Model):
    """The alias pointer pointing an index family to its active LIVE generation (ops.index_alias)."""

    index_family = models.TextField(primary_key=True)
    generation = models.TextField()
    previous_generation = models.TextField(null=True, blank=True)
    swapped_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'ops"."index_alias'

    def __str__(self) -> str:
        return f"{self.index_family} -> {self.generation}"


class Chunk(models.Model):
    """Retrieval unit combining lexical and dense representations (plc.chunk)."""

    pk = CompositePrimaryKey("index_generation", "chunk_id")
    chunk_id = models.TextField()
    index_generation = models.TextField()
    work_id = models.TextField()
    expression_key = models.TextField()
    anchor_ids = ArrayField(models.TextField())
    anchor_first = models.TextField()
    anchor_last = models.TextField()
    chunk_kind = models.TextField()
    rhetorical_role = models.TextField(null=True, blank=True)
    opinion_role = models.TextField(null=True, blank=True)
    context_header = models.TextField()
    text = models.TextField()
    text_hash = models.TextField()
    court_id = models.TextField(null=True, blank=True)
    court_level = models.TextField(null=True, blank=True)
    bench_strength = models.SmallIntegerField(null=True, blank=True)
    decision_date = models.DateField(null=True, blank=True)
    doc_type = models.TextField()
    binding_scope_tags = ArrayField(models.TextField(), default=list)
    cited_work_ids = ArrayField(models.TextField(), default=list)
    cited_provision_anchors = ArrayField(models.TextField(), default=list)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    in_force = models.BooleanField(null=True, blank=True)
    trust_label = models.TextField(default="PLC_OFFICIAL")
    rights_class = models.TextField()
    quality = models.JSONField(default=dict)
    body = models.JSONField(default=dict)
    doc_seq = models.BigIntegerField()
    pipeline_version = models.TextField()

    class Meta:
        managed = False
        db_table = 'plc"."chunk'

    def __str__(self) -> str:
        return f"{self.chunk_id} [{self.chunk_kind}] on {self.work_id}"


class IndexExpressionState(models.Model):
    """P2-internal state ledger tracking expression indexing lifecycle (plc.index_expression_state)."""

    serial_key = models.TextField(primary_key=True)  # {work_id}/{expression_key}
    accepted_parse_id = models.TextField(null=True, blank=True)
    doc_seq = models.BigIntegerField(default=1)
    content_digest = models.BinaryField(null=True, blank=True)
    enrichment_level = models.TextField(
        choices=[("NONE", "NONE"), ("BASE", "BASE"), ("FULL", "FULL")]
    )
    status = models.TextField(
        choices=[
            ("ACTIVE", "ACTIVE"),
            ("QUARANTINED", "QUARANTINED"),
            ("SUPERSEDED_REV", "SUPERSEDED_REV"),
            ("REKEYED", "REKEYED"),
        ]
    )
    last_quarantined_parse_id = models.TextField(null=True, blank=True)
    quarantine_reasons = models.JSONField(null=True, blank=True)
    pipeline_version = models.TextField()
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'plc"."index_expression_state'

    def __str__(self) -> str:
        return f"{self.serial_key} (seq={self.doc_seq}, status={self.status})"


class Summary(models.Model):
    """Anchored, entailment-checked digest aid (plc.summary) — Non-citable."""

    summary_id = models.TextField(primary_key=True)
    work_id = models.TextField()
    expression_key = models.TextField()
    level = models.TextField()
    scope_anchor_ids = ArrayField(models.TextField())
    fields = models.JSONField(null=True, blank=True)
    sentences = models.JSONField(default=list)
    review_state = models.TextField()
    pipeline_version = models.TextField()
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'plc"."summary'

    def __str__(self) -> str:
        return f"{self.summary_id} [{self.level}] on {self.work_id}"


class PrivateChunk(models.Model):
    """Private tenant-plane chunk with RLS isolation (tpl.private_chunk)."""

    pk = CompositePrimaryKey("tenant_id", "index_generation", "chunk_id")
    tenant_id = models.TextField()
    matter_id = models.TextField()
    chunk_id = models.TextField()
    index_generation = models.TextField()
    pdoc_id = models.TextField()
    pver = models.TextField()
    anchor_ids = ArrayField(models.TextField())
    text = models.TextField()
    trust_label = models.TextField()
    privilege_class = models.TextField()
    pipeline_version = models.TextField()

    class Meta:
        managed = False
        db_table = 'tpl"."private_chunk'

    def __str__(self) -> str:
        return f"{self.tenant_id}:{self.chunk_id}"
