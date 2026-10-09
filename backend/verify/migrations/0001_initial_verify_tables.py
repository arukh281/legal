"""Migration 0001: Initial verify tables (tpl.verification_report, tpl.claim_verification) from 03 §3.12."""

from django.db import migrations

SQL_FORWARD = """
-- 1. Pipeline version for verifier
INSERT INTO ops.pipeline_version (
  pipeline_version, component, semver, model_id, model_snapshot, endpoint_region, prompt_hash, code_sha, created_at
) VALUES (
  'p8.verifier@0.1.0|ladder_c0_c2_v1', 'p8.verifier', '0.1.0', NULL, NULL, NULL, NULL, 'git-s07', now()
) ON CONFLICT (pipeline_version) DO NOTHING;

-- 2. tpl.verification_report
CREATE TABLE tpl.verification_report (
  tenant_id text NOT NULL,
  report_id text NOT NULL,
  request_id text NOT NULL,
  subject jsonb NOT NULL,
  as_of_legal_date date NOT NULL,
  as_known_at timestamptz NOT NULL,
  graph_watermark bigint NOT NULL,
  anchor_generation text NOT NULL,
  verifier_version text NOT NULL REFERENCES ops.pipeline_version,
  gate text NOT NULL CHECK (gate IN ('PASS','PARTIAL','BLOCK')),
  section_gates jsonb,
  gate_reasons text[] NOT NULL DEFAULT '{}',
  withheld_claim_ids text[] NOT NULL DEFAULT '{}',
  withheld_sections text[] NOT NULL DEFAULT '{}',
  coverage jsonb NOT NULL,
  degradations jsonb NOT NULL DEFAULT '[]',
  calibration_state text NOT NULL DEFAULT 'UNCALIBRATED_PREVIEW' CHECK (calibration_state IN ('UNCALIBRATED_PREVIEW','CALIBRATED')),
  context_warnings text[],
  supersedes_report_id text,
  signature text NOT NULL,
  created_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, report_id)
);

ALTER TABLE tpl.verification_report ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.verification_report FORCE ROW LEVEL SECURITY;

CREATE POLICY verification_report_tenant_isolation ON tpl.verification_report
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

-- 3. tpl.claim_verification
CREATE TABLE tpl.claim_verification (
  tenant_id text NOT NULL,
  report_id text NOT NULL,
  claim_id text NOT NULL,
  claim_hash text NOT NULL,
  status text NOT NULL CHECK (status IN ('VERIFIED','PARTIAL','UNSUPPORTED','CONTRADICTED','BAD_LAW','UNVERIFIABLE')),
  display_band text NOT NULL CHECK (display_band IN ('VERIFIED','VERIFIED_WITH_CAVEAT','CHECK','WITHHELD')),
  calibrated_confidence real,
  confidence_stratum text NOT NULL DEFAULT 'UNCALIBRATED_PREVIEW',
  warrant jsonb NOT NULL,
  checks jsonb NOT NULL,
  reason_codes text[] NOT NULL DEFAULT '{}',
  narrowed_text text,
  suggested_anchor_ids text[],
  authority_snapshot jsonb,
  human_review jsonb,
  PRIMARY KEY (tenant_id, report_id, claim_id),
  CHECK (calibrated_confidence IS NULL OR confidence_stratum <> 'UNCALIBRATED_PREVIEW')
);

ALTER TABLE tpl.claim_verification ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.claim_verification FORCE ROW LEVEL SECURITY;

CREATE POLICY claim_verification_tenant_isolation ON tpl.claim_verification
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

-- 4. Grants
GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.verification_report TO app_rw, worker, admin_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.claim_verification TO app_rw, worker, admin_rw;
"""

SQL_REVERSE = """
DROP TABLE IF EXISTS tpl.claim_verification CASCADE;
DROP TABLE IF EXISTS tpl.verification_report CASCADE;
DELETE FROM ops.pipeline_version WHERE pipeline_version = 'p8.verifier@0.1.0|ladder_c0_c2_v1';
"""


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("reason", "0001_initial_reason_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
