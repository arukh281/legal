"""Django models for the Model Gateway (ops schema).

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.15
- docs/13_cross_cutting.md §4.2, §4.3
- DECISIONS.md (2026-10-01: CompositePrimaryKey, unprefixed call_id ULID)
"""

from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.fields.composite import CompositePrimaryKey
from django.utils import timezone


class ModelTaskContract(models.Model):
    """Model task contract specification (ops.model_task_contract)."""

    task_id = models.TextField(primary_key=True)
    owner_phase = models.TextField()
    input_schema = models.JSONField()
    output_schema = models.JSONField()
    max_input_chars = models.IntegerField()
    max_output_tokens = models.IntegerField()
    data_class_max = models.TextField(
        choices=[
            ("PUBLIC", "PUBLIC"),
            ("TENANT_CONFIDENTIAL", "TENANT_CONFIDENTIAL"),
            ("PRIVILEGED", "PRIVILEGED"),
        ]
    )
    allowed_trust_labels = ArrayField(models.TextField())
    tools_allowed = ArrayField(models.TextField(), default=list)
    eval = models.JSONField()
    latency_slo_ms = models.JSONField(null=True, blank=True)
    batch_ok = models.BooleanField()
    determinism = models.JSONField()
    escalation = models.JSONField(null=True, blank=True)
    prompt_variants = models.JSONField()

    class Meta:
        managed = False
        db_table = 'ops"."model_task_contract'

    def __str__(self) -> str:
        return self.task_id


class ModelEndpoint(models.Model):
    """Registered qualified model endpoint (ops.model_endpoint)."""

    endpoint_id = models.TextField(primary_key=True)
    provider = models.TextField()
    model_id = models.TextField()
    model_snapshot = models.TextField()
    processing_geo = models.TextField(
        choices=[
            ("IN", "IN"),
            ("APAC", "APAC"),
            ("US", "US"),
            ("GLOBAL", "GLOBAL"),
            ("EU", "EU"),
        ]
    )
    storage_geo = models.TextField(null=True, blank=True)
    zdr = models.BooleanField()
    data_class_max = models.TextField()
    price = models.JSONField()
    limits = models.JSONField()
    health = models.TextField(
        default="UP",
        choices=[("UP", "UP"), ("DEGRADED", "DEGRADED"), ("DOWN", "DOWN")],
    )
    qualified_tasks = models.JSONField(default=dict)

    class Meta:
        managed = False
        db_table = 'ops"."model_endpoint'

    def __str__(self) -> str:
        return f"{self.endpoint_id} ({self.processing_geo})"


class LLMCallRecord(models.Model):
    """Meters every model call attempt, failure, repair, and escalation (ops.llm_call_record)."""

    pk = CompositePrimaryKey("call_id", "created_at")
    call_id = models.TextField()
    trace_id = models.TextField()
    task_id = models.TextField()
    endpoint_id = models.TextField()
    pipeline_version = models.TextField()
    tenant_id = models.TextField(null=True, blank=True)
    matter_id = models.TextField(null=True, blank=True)
    dataclass = models.TextField()
    residency = models.TextField()
    processing_geo = models.TextField()
    purpose = models.TextField(null=True, blank=True)
    input_chars = models.IntegerField()
    output_chars = models.IntegerField()
    tokens_in = models.IntegerField()
    tokens_out = models.IntegerField()
    cache_read_tokens = models.IntegerField(default=0)
    usd = models.DecimalField(max_digits=10, decimal_places=6)
    latency_ms = models.IntegerField()
    schema_valid = models.BooleanField()
    repaired = models.BooleanField()
    escalated_from = models.TextField(null=True, blank=True)
    inputs_ref = models.TextField()
    outputs_ref = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'ops"."llm_call_record'

    def __str__(self) -> str:
        return f"LLMCall {self.call_id} [{self.task_id} -> {self.endpoint_id}]"
