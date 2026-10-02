"""Initial plc schema tables for document parsing, identity, and anchors (Session S05a).

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.3 & §3.4
- docs/01_master_architecture.md §5.3, §5.4, §5.5
"""

from __future__ import annotations

from django.db import migrations

UP_SQL = """
-- 1. plc.court (Court and Bench-Seat Registry)
CREATE TABLE IF NOT EXISTS plc.court (
  court_id text PRIMARY KEY,
  level text NOT NULL CHECK (level IN ('SC','HC','TRIBUNAL_APPELLATE','TRIBUNAL','DISTRICT','REGULATOR')),
  parent_ids text[] NOT NULL DEFAULT '{}',
  territory text,
  binding_scope_tags text[] NOT NULL DEFAULT '{}',
  valid_period daterange NOT NULL DEFAULT '[1950-01-26,)',
  meta jsonb NOT NULL DEFAULT '{}'
);

-- 2. plc.work (FRBR Work)
CREATE TABLE IF NOT EXISTS plc.work (
  work_id text PRIMARY KEY CHECK (work_id ~ '^wrk_[0-9A-HJKMNP-TV-Z]{26}$'),
  work_type text NOT NULL,
  status text NOT NULL CHECK (status IN ('ACTIVE','PROVISIONAL','STUB','EXPECTED','MERGED')),
  merged_into text REFERENCES plc.work(work_id),
  court_id text REFERENCES plc.court(court_id),
  decision_date date,
  title text,
  bench_strength smallint,
  access_restriction jsonb,
  integrity_flags text[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS work_title_trgm ON plc.work USING gin (title gin_trgm_ops);

-- 3. plc.legal_case
CREATE TABLE IF NOT EXISTS plc.legal_case (
  case_id text PRIMARY KEY CHECK (case_id ~ '^cas_[0-9A-HJKMNP-TV-Z]{26}$'),
  court_id text REFERENCES plc.court(court_id),
  case_type text,
  number text,
  year int,
  cnr text UNIQUE,
  diary_no text,
  status text,
  merged_into text
);

-- 4. plc.work_case
CREATE TABLE IF NOT EXISTS plc.work_case (
  work_id text REFERENCES plc.work(work_id),
  case_id text REFERENCES plc.legal_case(case_id),
  role text CHECK (role IN ('LEAD','CONNECTED','TAGGED')),
  PRIMARY KEY (work_id, case_id)
);

-- 5. plc.expression
CREATE TABLE IF NOT EXISTS plc.expression (
  work_id text REFERENCES plc.work(work_id),
  expression_key text NOT NULL,
  lang text NOT NULL,
  rev int,
  valid_from date,
  valid_to date,
  territory text,
  authoritative boolean NOT NULL,
  derived boolean NOT NULL DEFAULT false,
  verification text CHECK (verification IN ('ROUNDTRIP_OK','UNVERIFIED')),
  translation_of text,
  authority_basis text CHECK (authority_basis IN ('ORIGINAL','OLA_S7_HC_TRANSLATION','COURT_PUBLISHED_TRANSLATION','OFFICIAL_CONSOLIDATION','RECONSTRUCTED')),
  PRIMARY KEY (work_id, expression_key)
);

-- 6. plc.manifestation
CREATE TABLE IF NOT EXISTS plc.manifestation (
  manifestation_id text PRIMARY KEY CHECK (manifestation_id ~ '^man_[0-9A-HJKMNP-TV-Z]{26}$'),
  work_id text NOT NULL,
  expression_key text NOT NULL,
  source_id text REFERENCES plc.source(source_id),
  url text,
  raw_ids text[] NOT NULL,
  rights_class text NOT NULL,
  provenance_tier text NOT NULL,
  first_seen timestamptz,
  withdrawn_at timestamptz,
  suppressed_at timestamptz,
  FOREIGN KEY (work_id, expression_key) REFERENCES plc.expression(work_id, expression_key)
);

-- 7. plc.identifier_alias
CREATE TABLE IF NOT EXISTS plc.identifier_alias (
  scheme text NOT NULL,
  value_normalized text NOT NULL,
  target_id text NOT NULL,
  confidence real NOT NULL,
  source text NOT NULL,
  trust_tier text NOT NULL CHECK (trust_tier IN ('T0','T1','T2','T3','T4')),
  status text NOT NULL CHECK (status IN ('PENDING','ACTIVE','CONFLICT','REJECTED','SUPERSEDED')),
  first_seen timestamptz NOT NULL,
  evidence jsonb NOT NULL DEFAULT '{}',
  CHECK (scheme NOT IN ('URL','CITATION_STRING')),
  PRIMARY KEY (scheme, value_normalized, target_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS alias_one_active ON plc.identifier_alias (scheme, value_normalized) WHERE status = 'ACTIVE';

-- 8. plc.parse_run
CREATE TABLE IF NOT EXISTS plc.parse_run (
  parse_id text PRIMARY KEY CHECK (parse_id ~ '^par_[0-9A-HJKMNP-TV-Z]{26}$'),
  raw_ids text[] NOT NULL,
  manifestation_id text REFERENCES plc.manifestation(manifestation_id),
  work_id text NOT NULL REFERENCES plc.work(work_id),
  work_id_status text CHECK (work_id_status IN ('RESOLVED','PROVISIONAL')),
  expression_key text NOT NULL,
  doc_type text NOT NULL,
  parsed_doc_uri text NOT NULL,
  parsed_doc_sha256 text NOT NULL,
  quality jsonb NOT NULL,
  gate text NOT NULL CHECK (gate IN ('PASS','FLAGGED','QUARANTINED')),
  anchor_changes jsonb NOT NULL,
  supersedes_parse_id text REFERENCES plc.parse_run(parse_id),
  rights_class text NOT NULL,
  provenance_tier text NOT NULL,
  pipeline_version text NOT NULL REFERENCES ops.pipeline_version(pipeline_version),
  cost_usd numeric(10,5),
  created_at timestamptz NOT NULL
);

-- 9. plc.anchor
CREATE TABLE IF NOT EXISTS plc.anchor (
  anchor_id public_anchor_ref PRIMARY KEY,
  work_id text NOT NULL REFERENCES plc.work(work_id),
  expression_key text NOT NULL,
  fragment text NOT NULL,
  node_type text NOT NULL,
  number_as_printed text,
  numbering text CHECK (numbering IN ('EXPLICIT','SYNTHETIC')),
  text text NOT NULL,
  text_hash text NOT NULL,
  quote_prefix text,
  quote_suffix text,
  spans jsonb NOT NULL DEFAULT '[]',
  rhetorical_role jsonb,
  speaker text,
  opinion_role text CHECK (opinion_role IN ('MAJORITY','CONCURRING','DISSENT','REFERENCE_ORDER','UNKNOWN')),
  ocr_conf real,
  lang text NOT NULL,
  is_authoritative_expression boolean NOT NULL,
  state text NOT NULL DEFAULT 'LIVE' CHECK (state IN ('LIVE','TOMBSTONED')),
  forward_to text,
  first_parse_id text NOT NULL,
  last_parse_id text NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_anchor_work_expr ON plc.anchor (work_id, expression_key);

-- 10. plc.anchor_alias
CREATE TABLE IF NOT EXISTS plc.anchor_alias (
  old_anchor text,
  new_anchor text,
  method text CHECK (method IN ('NUM_EQ','HASH_EQ','NW_ALIGN','SPLIT','MERGE','RENUMBER','GRAMMAR_V11')),
  confidence real,
  parse_id text,
  recorded_at timestamptz NOT NULL,
  PRIMARY KEY (old_anchor, new_anchor)
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

-- Initial Court Registry Seed (observed courts from captured corpus)
INSERT INTO plc.court (court_id, level, parent_ids, territory, binding_scope_tags, valid_period, meta)
VALUES
  ('crt_IN_SC', 'SC', '{}', 'IN', ARRAY['ALL_INDIA'], '[1950-01-26,)', '{"name": "Supreme Court of India"}'::jsonb),
  ('crt_IN_NCLAT', 'TRIBUNAL_APPELLATE', ARRAY['crt_IN_SC'], 'IN', ARRAY['ALL_INDIA'], '[2016-06-01,)', '{"name": "National Company Law Appellate Tribunal, Principal Bench New Delhi"}'::jsonb),
  ('crt_IN_NCLAT_CHE', 'TRIBUNAL_APPELLATE', ARRAY['crt_IN_SC'], 'IN-TN', ARRAY['STATE:IN-TN'], '[2021-01-25,)', '{"name": "National Company Law Appellate Tribunal, Chennai Bench"}'::jsonb),
  ('crt_IN_NCLT_PB', 'TRIBUNAL', ARRAY['crt_IN_NCLAT'], 'IN-DL', ARRAY['ALL_INDIA'], '[2016-06-01,)', '{"name": "National Company Law Tribunal, Principal Bench New Delhi"}'::jsonb),
  ('crt_IN_NCLT_DEL', 'TRIBUNAL', ARRAY['crt_IN_NCLAT'], 'IN-DL', ARRAY['STATE:IN-DL'], '[2016-06-01,)', '{"name": "National Company Law Tribunal, New Delhi Bench"}'::jsonb),
  ('crt_IN_NCLT_MUM', 'TRIBUNAL', ARRAY['crt_IN_NCLAT'], 'IN-MH', ARRAY['STATE:IN-MH'], '[2016-06-01,)', '{"name": "National Company Law Tribunal, Mumbai Bench"}'::jsonb),
  ('crt_IN_NCLT_KOL', 'TRIBUNAL', ARRAY['crt_IN_NCLAT'], 'IN-WB', ARRAY['STATE:IN-WB'], '[2016-06-01,)', '{"name": "National Company Law Tribunal, Kolkata Bench"}'::jsonb),
  ('crt_IN_NCLT_CHE', 'TRIBUNAL', ARRAY['crt_IN_NCLAT'], 'IN-TN', ARRAY['STATE:IN-TN'], '[2016-06-01,)', '{"name": "National Company Law Tribunal, Chennai Bench"}'::jsonb),
  ('crt_IN_NCLT_AHM', 'TRIBUNAL', ARRAY['crt_IN_NCLAT'], 'IN-GJ', ARRAY['STATE:IN-GJ'], '[2016-06-01,)', '{"name": "National Company Law Tribunal, Ahmedabad Bench"}'::jsonb),
  ('crt_IN_NCLT_CHD', 'TRIBUNAL', ARRAY['crt_IN_NCLAT'], 'IN-CH', ARRAY['STATE:IN-CH', 'STATE:IN-PB', 'STATE:IN-HR'], '[2016-06-01,)', '{"name": "National Company Law Tribunal, Chandigarh Bench"}'::jsonb),
  ('crt_IN_NCLT_HYD', 'TRIBUNAL', ARRAY['crt_IN_NCLAT'], 'IN-TG', ARRAY['STATE:IN-TG', 'STATE:IN-AP'], '[2016-06-01,)', '{"name": "National Company Law Tribunal, Hyderabad Bench"}'::jsonb),
  ('crt_IN_NCLT_IND', 'TRIBUNAL', ARRAY['crt_IN_NCLAT'], 'IN-MP', ARRAY['STATE:IN-MP'], '[2016-06-01,)', '{"name": "National Company Law Tribunal, Indore Bench"}'::jsonb),
  ('crt_IN_NCLT_KOC', 'TRIBUNAL', ARRAY['crt_IN_NCLAT'], 'IN-KL', ARRAY['STATE:IN-KL', 'STATE:IN-LD'], '[2016-06-01,)', '{"name": "National Company Law Tribunal, Kochi Bench"}'::jsonb),
  ('crt_IN_NCLT_CUT', 'TRIBUNAL', ARRAY['crt_IN_NCLAT'], 'IN-OR', ARRAY['STATE:IN-OR'], '[2016-06-01,)', '{"name": "National Company Law Tribunal, Cuttack Bench"}'::jsonb),
  ('crt_IN_HC_BOM', 'HC', ARRAY['crt_IN_SC'], 'IN-MH', ARRAY['STATE:IN-MH', 'STATE:IN-GA'], '[1950-01-26,)', '{"name": "High Court of Judicature at Bombay"}'::jsonb),
  ('crt_IN_HC_DEL', 'HC', ARRAY['crt_IN_SC'], 'IN-DL', ARRAY['STATE:IN-DL'], '[1966-10-31,)', '{"name": "High Court of Delhi"}'::jsonb),
  ('crt_IN_HC_CAL', 'HC', ARRAY['crt_IN_SC'], 'IN-WB', ARRAY['STATE:IN-WB', 'STATE:IN-AN'], '[1950-01-26,)', '{"name": "High Court at Calcutta"}'::jsonb),
  ('crt_IN_HC_MAD', 'HC', ARRAY['crt_IN_SC'], 'IN-TN', ARRAY['STATE:IN-TN', 'STATE:IN-PY'], '[1950-01-26,)', '{"name": "High Court of Judicature at Madras"}'::jsonb)
ON CONFLICT (court_id) DO NOTHING;

-- Seed default pipeline_version for P1 parser
INSERT INTO ops.pipeline_version (pipeline_version, component, semver, code_sha, created_at)
VALUES ('p1.parser@0.1.0|det_v1', 'p1.parser', '0.1.0', 'det_v1', now())
ON CONFLICT (pipeline_version) DO NOTHING;

-- Subscribe p1_parser to raw.captured.v1
INSERT INTO ops.event_subscription (consumer, type, handler, lane, enabled)
VALUES ('p1_parser', 'raw.captured.v1', 'parse.consumer.handle_raw_captured', 'rt', true)
ON CONFLICT (consumer, type) DO UPDATE SET enabled = true;
"""

DOWN_SQL = """
DROP TABLE IF EXISTS plc.anchor_alias CASCADE;
DROP TABLE IF EXISTS plc.anchor CASCADE;
DROP TABLE IF EXISTS plc.parse_run CASCADE;
DROP TABLE IF EXISTS plc.identifier_alias CASCADE;
DROP TABLE IF EXISTS plc.manifestation CASCADE;
DROP TABLE IF EXISTS plc.expression CASCADE;
DROP TABLE IF EXISTS plc.work_case CASCADE;
DROP TABLE IF EXISTS plc.legal_case CASCADE;
DROP TABLE IF EXISTS plc.work CASCADE;
DROP TABLE IF EXISTS plc.court CASCADE;
"""


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("anchor_lib", "0001_anchor_domains"),
        ("ingest", "0001_initial_plc_source_capture"),
        ("ops", "0002_initial_ops_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=UP_SQL,
            reverse_sql=DOWN_SQL,
        ),
    ]
