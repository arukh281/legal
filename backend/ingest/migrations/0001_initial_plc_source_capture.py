"""Initial migration creating plc schema tables for source capture and legal profile.

Matches normative DDL from docs/mvp/03_data_model_and_contracts.md §3.2
plus plc.legal_profile, plc.host_rate_limit, and plc.crawl_checkpoint (MVP additions).
"""

from django.db import migrations

UP_SQL = """
-- 1. plc.source
CREATE TABLE IF NOT EXISTS plc.source (
  source_id text PRIMARY KEY,
  name text NOT NULL,
  base_url text,
  provenance_tier text NOT NULL,
  default_rights_class text NOT NULL,
  terms_ref text,
  hotness text CHECK (hotness IN ('HOT','WARM','COOL')),
  schedule_cron text,
  enabled boolean DEFAULT true
);

-- 2. plc.raw_blob
CREATE TABLE IF NOT EXISTS plc.raw_blob (
  raw_id text PRIMARY KEY CHECK (raw_id ~ '^sha256:[0-9a-f]{64}$'),
  storage_uri text NOT NULL,
  byte_size bigint NOT NULL,
  content_type text,
  first_seen_at timestamptz NOT NULL
);

-- 3. plc.capture
CREATE TABLE IF NOT EXISTS plc.capture (
  capture_id text PRIMARY KEY CHECK (capture_id ~ '^cap_[0-9A-HJKMNP-TV-Z]{26}$'),
  raw_id text NOT NULL REFERENCES plc.raw_blob(raw_id),
  source_id text NOT NULL REFERENCES plc.source(source_id),
  source_record_key text NOT NULL,
  url text,
  fetched_at timestamptz NOT NULL,
  change_kind text NOT NULL CHECK (change_kind IN ('NEW','CHANGED','UNCHANGED','DELETED','REAPPEARED','METADATA_CHANGED','SUPPRESSED')),
  prior_raw_id text,
  source_metadata jsonb NOT NULL DEFAULT '{}',
  rights_class text NOT NULL,
  provenance_tier text NOT NULL,
  fetch_context jsonb,
  flags jsonb,
  crawl_run_id text
);
CREATE INDEX IF NOT EXISTS idx_capture_source_rec_fetched ON plc.capture (source_id, source_record_key, fetched_at DESC);

-- 4. plc.source_health
CREATE TABLE IF NOT EXISTS plc.source_health (
  source_id text REFERENCES plc.source(source_id),
  observed_at timestamptz,
  status text CHECK (status IN ('OK','DEGRADED','DOWN','BLOCKED')),
  freshness_lag_p95_min int,
  last_success_at timestamptz,
  coverage_estimate real,
  expected_pending int,
  incident_id text,
  PRIMARY KEY (source_id, observed_at)
);

-- 5. plc.legal_profile (MVP Addition)
CREATE TABLE IF NOT EXISTS plc.legal_profile (
  profile_id text PRIMARY KEY CHECK (profile_id ~ '^lp_[0-9A-HJKMNP-TV-Z]{26}$'),
  source_id text NOT NULL REFERENCES plc.source(source_id),
  status text NOT NULL CHECK (status IN ('PROVISIONAL', 'APPROVED', 'SUSPENDED')),
  permitted_access_modes text[] NOT NULL DEFAULT '{"OPEN"}',
  rate_limit_delay_seconds real NOT NULL DEFAULT 3.0,
  allowed_hours_start_ist smallint NOT NULL DEFAULT 0 CHECK (allowed_hours_start_ist >= 0 AND allowed_hours_start_ist <= 23),
  allowed_hours_end_ist smallint NOT NULL DEFAULT 24 CHECK (allowed_hours_end_ist >= 1 AND allowed_hours_end_ist <= 24),
  backfill_allowed_start_ist smallint NOT NULL DEFAULT 23 CHECK (backfill_allowed_start_ist >= 0 AND backfill_allowed_start_ist <= 23),
  backfill_allowed_end_ist smallint NOT NULL DEFAULT 7 CHECK (backfill_allowed_end_ist >= 0 AND backfill_allowed_end_ist <= 23),
  backfill_night_only boolean NOT NULL DEFAULT true,
  tou_raw_id text REFERENCES plc.raw_blob(raw_id),
  robots_raw_id text REFERENCES plc.raw_blob(raw_id),
  copyright_raw_id text REFERENCES plc.raw_blob(raw_id),
  terms_ref text NOT NULL,
  counsel_question_refs text[] NOT NULL DEFAULT '{}',
  kill_switch boolean NOT NULL DEFAULT false,
  kill_reason text,
  approved_by text,
  approved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  notes text,
  CHECK (expires_at <= coalesce(approved_at, created_at) + interval '180 days'),
  CHECK (status <> 'APPROVED' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)),
  CHECK (permitted_access_modes <@ ARRAY['OPEN','BULK_DATASET','LICENSED_API','HUMAN_ASSISTED','PARTNER_CONTRIBUTED']::text[])
);
CREATE INDEX IF NOT EXISTS idx_legal_profile_source_status ON plc.legal_profile (source_id, status);
CREATE UNIQUE INDEX IF NOT EXISTS unique_active_legal_profile_per_source ON plc.legal_profile (source_id) WHERE status <> 'SUSPENDED';

-- 6. plc.host_rate_limit (Cross-Process Rate Limiting)
CREATE TABLE IF NOT EXISTS plc.host_rate_limit (
  host text PRIMARY KEY,
  last_request_at timestamptz NOT NULL,
  min_delay_seconds real NOT NULL DEFAULT 3.0
);

-- 7. plc.crawl_checkpoint (Resumable Crawl Runs)
CREATE TABLE IF NOT EXISTS plc.crawl_checkpoint (
  crawl_run_id text NOT NULL,
  source_id text NOT NULL REFERENCES plc.source(source_id),
  section text NOT NULL,
  page_number int NOT NULL,
  items_count int NOT NULL DEFAULT 0,
  unchanged_streak int NOT NULL DEFAULT 0,
  completed_at timestamptz NOT NULL DEFAULT now(),
  cursor_data jsonb,
  PRIMARY KEY (crawl_run_id, section, page_number)
);

-- Role grants
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_rw') THEN
    GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA plc TO app_rw;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'worker') THEN
    GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA plc TO worker;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'plc_writer') THEN
    GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA plc TO plc_writer;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin_rw') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA plc TO admin_rw;
  END IF;
END $$;
"""

DOWN_SQL = """
DROP TABLE IF EXISTS plc.crawl_checkpoint CASCADE;
DROP TABLE IF EXISTS plc.host_rate_limit CASCADE;
DROP TABLE IF EXISTS plc.legal_profile CASCADE;
DROP TABLE IF EXISTS plc.source_health CASCADE;
DROP TABLE IF EXISTS plc.capture CASCADE;
DROP TABLE IF EXISTS plc.raw_blob CASCADE;
DROP TABLE IF EXISTS plc.source CASCADE;
"""


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("ops", "0001_initial_extensions_and_schemas"),
    ]

    operations = [
        migrations.RunSQL(
            sql=UP_SQL,
            reverse_sql=DOWN_SQL,
        ),
    ]
