"""Migration 0002: Add plc.citation_mention and plc.identity_merge_ledger (Session S05b).

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.3 & §3.4
- docs/01_master_architecture.md §5.4, §6.3, §7.1
"""

from __future__ import annotations

from django.db import migrations

UP_SQL = """
-- 1. plc.citation_mention (Resolution result of CitationMention per 01 §7.1 / 03 §3.4)
CREATE TABLE IF NOT EXISTS plc.citation_mention (
  mention_id text PRIMARY KEY CHECK (mention_id ~ '^cm_[0-9A-HJKMNP-TV-Z]{26}$'),
  parse_id text NOT NULL REFERENCES plc.parse_run(parse_id),
  citing_work_id text NOT NULL REFERENCES plc.work(work_id),
  anchor_id text NOT NULL,
  raw_text text NOT NULL,
  mention_kind text NOT NULL,
  scheme text,
  normalized text,
  pin jsonb,
  resolved_target_id text,
  resolution_confidence real,
  resolution_method text,
  temporal_check text CHECK (temporal_check IN ('OK','CITED_AFTER_CITING','UNKNOWN'))
);
CREATE INDEX IF NOT EXISTS idx_citation_mention_target ON plc.citation_mention (resolved_target_id);
CREATE INDEX IF NOT EXISTS idx_citation_mention_parse ON plc.citation_mention (parse_id);
CREATE INDEX IF NOT EXISTS idx_citation_mention_citing_work ON plc.citation_mention (citing_work_id);

-- 2. plc.identity_merge_ledger (Identity merge/split source of truth per 03 §3.3 / 01 §6.3)
CREATE TABLE IF NOT EXISTS plc.identity_merge_ledger (
  event_id text PRIMARY KEY,
  kind text CHECK (kind IN ('WORK','CASE','ALIAS')),
  op text CHECK (op IN ('MERGE','SPLIT')),
  from_id text NOT NULL,
  to_id text NOT NULL,
  reason text,
  confidence real,
  reversible_until timestamptz,
  recorded_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_merge_ledger_from_id ON plc.identity_merge_ledger (from_id);
CREATE INDEX IF NOT EXISTS idx_merge_ledger_to_id ON plc.identity_merge_ledger (to_id);

-- Role grants
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_rw') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON plc.citation_mention TO app_rw;
    GRANT SELECT, INSERT, UPDATE, DELETE ON plc.identity_merge_ledger TO app_rw;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'worker') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON plc.citation_mention TO worker;
    GRANT SELECT, INSERT, UPDATE, DELETE ON plc.identity_merge_ledger TO worker;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'plc_writer') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON plc.citation_mention TO plc_writer;
    GRANT SELECT, INSERT, UPDATE, DELETE ON plc.identity_merge_ledger TO plc_writer;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin_rw') THEN
    GRANT SELECT, INSERT, UPDATE, DELETE ON plc.citation_mention TO admin_rw;
    GRANT SELECT, INSERT, UPDATE, DELETE ON plc.identity_merge_ledger TO admin_rw;
  END IF;
END $$;

-- Seed pipeline_version for S05b citation extraction
INSERT INTO ops.pipeline_version (pipeline_version, component, semver, code_sha, created_at)
VALUES ('p1.citation@0.1.0|det_v1', 'p1.citation', '0.1.0', 'det_v1', now())
ON CONFLICT (pipeline_version) DO NOTHING;
"""

DOWN_SQL = """
DROP TABLE IF EXISTS plc.citation_mention CASCADE;
DROP TABLE IF EXISTS plc.identity_merge_ledger CASCADE;
DELETE FROM ops.pipeline_version WHERE pipeline_version = 'p1.citation@0.1.0|det_v1';
"""


class Migration(migrations.Migration):
    dependencies = [
        ("parse", "0001_initial_parse_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=UP_SQL,
            reverse_sql=DOWN_SQL,
        ),
    ]
