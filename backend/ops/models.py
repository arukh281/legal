"""Django models for operations and lineage schema (ops).

Matches verbatim DDL from docs/mvp/03_data_model_and_contracts.md §3.1 and §3.16.
All models have managed = False because tables are created by verbatim SQL migrations.
"""

from django.db import models


class PipelineVersion(models.Model):
    pipeline_version = models.TextField(primary_key=True)
    component = models.TextField()
    semver = models.TextField()
    model_id = models.TextField(null=True, blank=True)
    model_snapshot = models.TextField(null=True, blank=True)
    endpoint_region = models.TextField(null=True, blank=True)
    prompt_hash = models.TextField(null=True, blank=True)
    code_sha = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "ops.pipeline_version"


class EventOutbox(models.Model):
    id = models.TextField(primary_key=True)
    specversion = models.TextField(default="1.0")
    type = models.TextField()
    source = models.TextField()
    time = models.DateTimeField()
    subject = models.TextField(null=True, blank=True)
    datacontenttype = models.TextField(default="application/json")
    dataschema = models.TextField()
    tenantid = models.TextField(null=True, blank=True)
    dataclass = models.TextField()
    traceparent = models.TextField(null=True, blank=True)
    causationid = models.TextField(null=True, blank=True)
    idempotencykey = models.TextField()
    schemaversion = models.TextField()
    datasig = models.TextField(null=True, blank=True)
    data = models.JSONField()
    topic = models.TextField()
    partition_key = models.TextField()
    lane = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "ops.event_outbox"
        unique_together = (("source", "id"),)


class EventSubscription(models.Model):
    consumer = models.TextField(primary_key=True)
    type = models.TextField()
    handler = models.TextField()
    lane = models.TextField(null=True, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = "ops.event_subscription"
        unique_together = (("consumer", "type"),)


class EventInbox(models.Model):
    consumer = models.TextField()
    idempotencykey = models.TextField(primary_key=True)
    payload_hash = models.BinaryField()
    event_id = models.TextField()
    processed_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "ops.event_inbox"
        unique_together = (("consumer", "idempotencykey"),)


class EventParked(models.Model):
    consumer = models.TextField()
    event_id = models.TextField(primary_key=True)
    reason = models.TextField()
    parked_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "ops.event_parked"
        unique_together = (("consumer", "event_id"),)


class JobChain(models.Model):
    job_id = models.TextField(primary_key=True)
    kind = models.TextField()
    tenant_id = models.TextField(null=True, blank=True)
    matter_id = models.TextField(null=True, blank=True)
    idempotency_key = models.TextField(unique=True)
    status = models.TextField()
    request = models.JSONField()
    budget = models.JSONField()
    spent = models.JSONField(default=dict)
    current_step = models.TextField(null=True, blank=True)
    context_version = models.BigIntegerField(null=True, blank=True)
    as_known_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "ops.job_chain"


class JobStep(models.Model):
    step_key = models.TextField(primary_key=True)
    job_id = models.TextField()
    step = models.TextField()
    attempt = models.IntegerField(default=1)
    status = models.TextField()
    input_hashes = models.JSONField()
    output = models.JSONField(null=True, blank=True)
    output_ref = models.TextField(null=True, blank=True)
    pipeline_version = models.TextField(null=True, blank=True)
    procrastinate_job_id = models.BigIntegerField(null=True, blank=True)
    heartbeat_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error = models.JSONField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "ops.job_step"
        unique_together = (("job_id", "step", "attempt"),)


class JobSignal(models.Model):
    job_id = models.TextField()
    signal = models.TextField()
    payload = models.JSONField()
    received_at = models.DateTimeField(primary_key=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "ops.job_signal"
        unique_together = (("job_id", "signal", "received_at"),)
