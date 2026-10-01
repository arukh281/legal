"""Django models for source capture, raw blobs, and legal profiles (plc schema).

Matches verbatim DDL from docs/mvp/03_data_model_and_contracts.md §3.2 and Session S04 additions.
All models have managed = False because tables are created by verbatim SQL migrations.
"""

from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.fields.composite import CompositePrimaryKey

from anchor_lib.models import DomainModel, PrefixedULIDField


class Source(models.Model):
    """Registry of crawled/ingested portals (plc.source)."""

    source_id = models.TextField(primary_key=True)
    name = models.TextField()
    base_url = models.TextField(null=True, blank=True)
    provenance_tier = models.TextField()
    default_rights_class = models.TextField()
    terms_ref = models.TextField(null=True, blank=True)
    hotness = models.TextField(null=True, blank=True)
    schedule_cron = models.TextField(null=True, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'plc"."source'

    def __str__(self) -> str:
        return f"Source({self.source_id})"


class RawBlob(models.Model):
    """Content-addressed bytes in S3 (plc.raw_blob)."""

    raw_id = models.TextField(primary_key=True)
    storage_uri = models.TextField()
    byte_size = models.BigIntegerField()
    content_type = models.TextField(null=True, blank=True)
    first_seen_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'plc"."raw_blob'

    def __str__(self) -> str:
        return f"RawBlob({self.raw_id})"


class Capture(DomainModel):
    """One fetch observation = the raw.captured.v1 payload (plc.capture)."""

    capture_id = PrefixedULIDField(prefix="cap", primary_key=True)
    raw = models.ForeignKey(RawBlob, on_delete=models.PROTECT, db_column="raw_id")
    source = models.ForeignKey(Source, on_delete=models.PROTECT, db_column="source_id")
    source_record_key = models.TextField()
    url = models.TextField(null=True, blank=True)
    fetched_at = models.DateTimeField()
    change_kind = models.TextField()
    prior_raw_id = models.TextField(null=True, blank=True)
    source_metadata = models.JSONField(default=dict)
    rights_class = models.TextField()
    provenance_tier = models.TextField()
    fetch_context = models.JSONField(null=True, blank=True)
    flags = models.JSONField(null=True, blank=True)
    crawl_run_id = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'plc"."capture'

    def __str__(self) -> str:
        return f"Capture({self.capture_id}, {self.source_id}, {self.change_kind})"


class SourceHealth(models.Model):
    """Source health history (plc.source_health)."""

    pk = CompositePrimaryKey("source_id", "observed_at")
    source = models.ForeignKey(Source, on_delete=models.PROTECT, db_column="source_id")
    observed_at = models.DateTimeField()
    status = models.TextField()
    freshness_lag_p95_min = models.IntegerField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    coverage_estimate = models.FloatField(null=True, blank=True)
    expected_pending = models.IntegerField(null=True, blank=True)
    incident_id = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'plc"."source_health'

    def __str__(self) -> str:
        return f"SourceHealth({self.source_id}, {self.status}, {self.observed_at})"


class LegalProfile(DomainModel):
    """Legal gate governance profile per source (plc.legal_profile).

    Never updated in place: changes create a new row and SUSPEND the old one.
    """

    profile_id = PrefixedULIDField(prefix="lp", primary_key=True)
    source = models.ForeignKey(Source, on_delete=models.PROTECT, db_column="source_id")
    status = models.TextField()
    permitted_access_modes: list[str] = ArrayField(models.TextField(), default=list)  # type: ignore[assignment]
    rate_limit_delay_seconds = models.FloatField(default=3.0)
    allowed_hours_start_ist = models.SmallIntegerField(default=0)
    allowed_hours_end_ist = models.SmallIntegerField(default=24)
    backfill_allowed_start_ist = models.SmallIntegerField(default=23)
    backfill_allowed_end_ist = models.SmallIntegerField(default=7)
    backfill_night_only = models.BooleanField(default=True)
    tou_raw = models.ForeignKey(
        RawBlob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="tou_raw_id",
        related_name="tou_profiles",
    )
    robots_raw = models.ForeignKey(
        RawBlob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="robots_raw_id",
        related_name="robots_profiles",
    )
    copyright_raw = models.ForeignKey(
        RawBlob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="copyright_raw_id",
        related_name="copyright_profiles",
    )
    terms_ref = models.TextField()
    counsel_question_refs: list[str] = ArrayField(models.TextField(), default=list)  # type: ignore[assignment]
    kill_switch = models.BooleanField(default=False)
    kill_reason = models.TextField(null=True, blank=True)
    approved_by = models.TextField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    notes = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'plc"."legal_profile'

    def __str__(self) -> str:
        return f"LegalProfile({self.profile_id}, {self.source_id}, {self.status})"


class HostRateLimit(models.Model):
    """Cross-process per-host rate limiting table (plc.host_rate_limit)."""

    host = models.TextField(primary_key=True)
    last_request_at = models.DateTimeField()
    min_delay_seconds = models.FloatField(default=3.0)

    class Meta:
        managed = False
        db_table = 'plc"."host_rate_limit'


class CrawlCheckpoint(models.Model):
    """Resumable crawl checkpoint per page (plc.crawl_checkpoint)."""

    pk = CompositePrimaryKey("crawl_run_id", "section", "page_number")
    crawl_run_id = models.TextField()
    source = models.ForeignKey(Source, on_delete=models.PROTECT, db_column="source_id")
    section = models.TextField()
    page_number = models.IntegerField()
    items_count = models.IntegerField(default=0)
    unchanged_streak = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)
    cursor_data = models.JSONField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'plc"."crawl_checkpoint'
