"""Django models for document parsing, identity, and anchors (plc schema).

Matches verbatim DDL from docs/mvp/03_data_model_and_contracts.md §3.3 & §3.4.
All models have managed = False because tables are created by verbatim SQL migrations.
"""

from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.fields.composite import CompositePrimaryKey

from anchor_lib.models import DomainModel, PrefixedULIDField
from ingest.models import Source
from ops.models import PipelineVersion


class Court(models.Model):
    """Court and Bench-Seat Registry (plc.court)."""

    court_id = models.TextField(primary_key=True)
    level = models.TextField()
    parent_ids: list[str] = ArrayField(models.TextField(), default=list)  # type: ignore[assignment]
    territory = models.TextField(null=True, blank=True)
    binding_scope_tags: list[str] = ArrayField(models.TextField(), default=list)  # type: ignore[assignment]
    meta = models.JSONField(default=dict)

    class Meta:
        managed = False
        db_table = 'plc"."court'

    def __str__(self) -> str:
        return f"Court({self.court_id})"


class Work(DomainModel):
    """FRBR Work (plc.work); P1 is the sole writer of identity."""

    work_id = PrefixedULIDField(prefix="wrk", primary_key=True)
    work_type = models.TextField()
    status = models.TextField()
    merged_into = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="merged_into",
    )
    court = models.ForeignKey(
        Court,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="court_id",
    )
    decision_date = models.DateField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    bench_strength = models.SmallIntegerField(null=True, blank=True)
    access_restriction = models.JSONField(null=True, blank=True)
    integrity_flags: list[str] = ArrayField(models.TextField(), default=list)  # type: ignore[assignment]
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'plc"."work'

    def __str__(self) -> str:
        return f"Work({self.work_id}, {self.work_type}, {self.status})"


class LegalCase(DomainModel):
    """Legal proceeding / Case entity (plc.legal_case)."""

    case_id = PrefixedULIDField(prefix="cas", primary_key=True)
    court = models.ForeignKey(
        Court,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="court_id",
    )
    case_type = models.TextField(null=True, blank=True)
    number = models.TextField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    cnr = models.TextField(unique=True, null=True, blank=True)
    diary_no = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    merged_into = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'plc"."legal_case'

    def __str__(self) -> str:
        return f"LegalCase({self.case_id}, {self.case_type} {self.number}/{self.year})"


class WorkCase(models.Model):
    """Join table between Work and LegalCase (plc.work_case)."""

    pk = CompositePrimaryKey("work_id", "case_id")
    work = models.ForeignKey(Work, on_delete=models.CASCADE, db_column="work_id")
    case = models.ForeignKey(LegalCase, on_delete=models.CASCADE, db_column="case_id")
    role = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'plc"."work_case'

    def __str__(self) -> str:
        return f"WorkCase({self.work_id}, {self.case_id}, {self.role})"


class Expression(models.Model):
    """Work Expression (plc.expression)."""

    pk = CompositePrimaryKey("work_id", "expression_key")
    work = models.ForeignKey(Work, on_delete=models.CASCADE, db_column="work_id")
    expression_key = models.TextField()
    lang = models.TextField()
    rev = models.IntegerField(null=True, blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    territory = models.TextField(null=True, blank=True)
    authoritative = models.BooleanField()
    derived = models.BooleanField(default=False)
    verification = models.TextField(null=True, blank=True)
    translation_of = models.TextField(null=True, blank=True)
    authority_basis = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'plc"."expression'

    def __str__(self) -> str:
        return f"Expression({self.work_id}/{self.expression_key})"


class Manifestation(DomainModel):
    """Manifestation of an Expression (plc.manifestation)."""

    manifestation_id = PrefixedULIDField(prefix="man", primary_key=True)
    work = models.ForeignKey(Work, on_delete=models.PROTECT, db_column="work_id")
    expression_key = models.TextField()
    source = models.ForeignKey(
        Source,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="source_id",
    )
    url = models.TextField(null=True, blank=True)
    raw_ids: list[str] = ArrayField(models.TextField())  # type: ignore[assignment]
    rights_class = models.TextField()
    provenance_tier = models.TextField()
    first_seen = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    suppressed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'plc"."manifestation'

    def __str__(self) -> str:
        return f"Manifestation({self.manifestation_id}, {self.work_id}/{self.expression_key})"


class IdentifierAlias(models.Model):
    """Natural-key aliases with trust tiers T0–T4 (plc.identifier_alias)."""

    pk = CompositePrimaryKey("scheme", "value_normalized", "target_id")
    scheme = models.TextField()
    value_normalized = models.TextField()
    target_id = models.TextField()
    confidence = models.FloatField()
    source = models.TextField()
    trust_tier = models.TextField()
    status = models.TextField()
    first_seen = models.DateTimeField()
    evidence = models.JSONField(default=dict)

    class Meta:
        managed = False
        db_table = 'plc"."identifier_alias'

    def __str__(self) -> str:
        return f"IdentifierAlias({self.scheme}, {self.value_normalized} -> {self.target_id})"


class ParseRun(DomainModel):
    """Record of a document parse run (plc.parse_run)."""

    parse_id = PrefixedULIDField(prefix="par", primary_key=True)
    raw_ids: list[str] = ArrayField(models.TextField())  # type: ignore[assignment]
    manifestation = models.ForeignKey(
        Manifestation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="manifestation_id",
    )
    work = models.ForeignKey(Work, on_delete=models.PROTECT, db_column="work_id")
    work_id_status = models.TextField(null=True, blank=True)
    expression_key = models.TextField()
    doc_type = models.TextField()
    parsed_doc_uri = models.TextField()
    parsed_doc_sha256 = models.TextField()
    quality = models.JSONField()
    gate = models.TextField()
    anchor_changes = models.JSONField()
    supersedes_parse_id = models.TextField(null=True, blank=True)
    rights_class = models.TextField()
    provenance_tier = models.TextField()
    pipeline_version = models.ForeignKey(
        PipelineVersion,
        on_delete=models.PROTECT,
        db_column="pipeline_version",
    )
    cost_usd = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'plc"."parse_run'

    def __str__(self) -> str:
        return f"ParseRun({self.parse_id}, {self.work_id}, {self.gate})"


class Anchor(models.Model):
    """The unit every claim traces to (plc.anchor). Never deleted, never reused."""

    anchor_id = models.CharField(max_length=512, primary_key=True)
    work = models.ForeignKey(Work, on_delete=models.PROTECT, db_column="work_id")
    expression_key = models.TextField()
    fragment = models.TextField()
    node_type = models.TextField()
    number_as_printed = models.TextField(null=True, blank=True)
    numbering = models.TextField(null=True, blank=True)
    text = models.TextField()
    text_hash = models.TextField()
    quote_prefix = models.TextField(null=True, blank=True)
    quote_suffix = models.TextField(null=True, blank=True)
    spans = models.JSONField(default=list)
    rhetorical_role = models.JSONField(null=True, blank=True)
    speaker = models.TextField(null=True, blank=True)
    opinion_role = models.TextField(null=True, blank=True)
    ocr_conf = models.FloatField(null=True, blank=True)
    lang = models.TextField()
    is_authoritative_expression = models.BooleanField()
    state = models.TextField(default="LIVE")
    forward_to = models.TextField(null=True, blank=True)
    first_parse_id = models.TextField()
    last_parse_id = models.TextField()

    class Meta:
        managed = False
        db_table = 'plc"."anchor'

    def __str__(self) -> str:
        return f"Anchor({self.anchor_id}, {self.state})"


class AnchorAlias(models.Model):
    """Forward alias mapping when an anchor changes across re-parses (plc.anchor_alias)."""

    pk = CompositePrimaryKey("old_anchor", "new_anchor")
    old_anchor = models.TextField()
    new_anchor = models.TextField()
    method = models.TextField()
    confidence = models.FloatField(null=True, blank=True)
    parse_id = models.TextField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'plc"."anchor_alias'

    def __str__(self) -> str:
        return f"AnchorAlias({self.old_anchor} -> {self.new_anchor} via {self.method})"


class CitationMention(DomainModel):
    """Resolution result of a CitationMention in an order (plc.citation_mention)."""

    mention_id = PrefixedULIDField(prefix="cm", primary_key=True)
    parse = models.ForeignKey(ParseRun, on_delete=models.CASCADE, db_column="parse_id")
    citing_work = models.ForeignKey(Work, on_delete=models.PROTECT, db_column="citing_work_id")
    anchor_id = models.TextField()
    raw_text = models.TextField()
    mention_kind = models.TextField()
    scheme = models.TextField(null=True, blank=True)
    normalized = models.TextField(null=True, blank=True)
    pin = models.JSONField(null=True, blank=True)
    resolved_target_id = models.TextField(null=True, blank=True)
    resolution_confidence = models.FloatField(null=True, blank=True)
    resolution_method = models.TextField(null=True, blank=True)
    temporal_check = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'plc"."citation_mention'

    def __str__(self) -> str:
        return f"CitationMention({self.mention_id}, {self.raw_text} -> {self.resolved_target_id})"


class IdentityMergeLedger(models.Model):
    """Ledger of identity merges and splits (plc.identity_merge_ledger)."""

    event_id = models.TextField(primary_key=True)
    kind = models.TextField()
    op = models.TextField()
    from_id = models.TextField()
    to_id = models.TextField()
    reason = models.TextField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    reversible_until = models.DateTimeField(null=True, blank=True)
    recorded_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'plc"."identity_merge_ledger'

    def __str__(self) -> str:
        return f"IdentityMergeLedger({self.event_id}, {self.op} {self.kind}: {self.from_id} -> {self.to_id})"
