"""Migration 0001: Initial retrieve tables (tpl.research_query, tpl.evidence_bundle) from 03 §3.11."""

from django.db import migrations

SQL_FORWARD = """
-- 1. Pipeline version for retriever
INSERT INTO ops.pipeline_version (
  pipeline_version, component, semver, model_id, model_snapshot, endpoint_region, prompt_hash, code_sha, created_at
) VALUES (
  'p5.retriever@0.1.0|lexical_v1', 'p5.retriever', '0.1.0', NULL, NULL, NULL, NULL, 'git-s07', now()
) ON CONFLICT (pipeline_version) DO NOTHING;

-- 2. tpl.research_query
CREATE TABLE tpl.research_query (
  tenant_id text NOT NULL,
  query_id text NOT NULL,
  matter_id text,
  user_id text NOT NULL,
  text text NOT NULL,
  mode text NOT NULL CHECK (mode IN ('QUICK','STANDARD','DEEP')),
  as_of_legal_date date NOT NULL,
  as_known_at timestamptz NOT NULL,
  forum jsonb,
  perspective text NOT NULL,
  stance_target text NOT NULL DEFAULT 'BOTH',
  request jsonb NOT NULL,
  answer jsonb,
  verification_report_id text,
  created_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, query_id)
);

ALTER TABLE tpl.research_query ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.research_query FORCE ROW LEVEL SECURITY;

CREATE POLICY research_query_tenant_isolation ON tpl.research_query
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

-- 3. tpl.evidence_bundle
CREATE TABLE tpl.evidence_bundle (
  tenant_id text NOT NULL,
  bundle_id text NOT NULL,
  query_id text NOT NULL,
  as_of_legal_date date NOT NULL,
  as_known_at timestamptz NOT NULL,
  index_generation text NOT NULL,
  graph_watermark bigint NOT NULL,
  pipeline_version text NOT NULL REFERENCES ops.pipeline_version,
  issues jsonb NOT NULL,
  items jsonb NOT NULL,
  coverage jsonb NOT NULL,
  warnings jsonb NOT NULL DEFAULT '[]',
  searched jsonb NOT NULL,
  trace_id text NOT NULL,
  created_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, bundle_id)
);

ALTER TABLE tpl.evidence_bundle ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.evidence_bundle FORCE ROW LEVEL SECURITY;

CREATE POLICY evidence_bundle_tenant_isolation ON tpl.evidence_bundle
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

-- 4. Grants
GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.research_query TO app_rw, worker, admin_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.evidence_bundle TO app_rw, worker, admin_rw;
"""

SQL_REVERSE = """
DROP TABLE IF EXISTS tpl.evidence_bundle CASCADE;
DROP TABLE IF EXISTS tpl.research_query CASCADE;
DELETE FROM ops.pipeline_version WHERE pipeline_version = 'p5.retriever@0.1.0|lexical_v1';
"""


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("index", "0009_fix_voyage_endpoint_and_subscriptions"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
