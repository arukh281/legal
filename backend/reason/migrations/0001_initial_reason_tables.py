"""Migration 0001: Initial reason tables (tpl.claim), pipeline version, and task contract from 03 §3.11, §3.15."""

from django.db import migrations

SQL_FORWARD = """
-- 1. Pipeline version for reasoner
INSERT INTO ops.pipeline_version (
  pipeline_version, component, semver, model_id, model_snapshot, endpoint_region, prompt_hash, code_sha, created_at
) VALUES (
  'p6.reasoner@0.1.0|qa_synthesis_v1', 'p6.reasoner', '0.1.0', NULL, NULL, NULL, NULL, 'git-s07', now()
) ON CONFLICT (pipeline_version) DO NOTHING;

-- 2. tpl.claim
CREATE TABLE tpl.claim (
  tenant_id text NOT NULL,
  claim_id text NOT NULL,
  owner_kind text NOT NULL CHECK (owner_kind IN ('MEMO','ANSWER','DRAFT')),
  owner_id text NOT NULL,
  section text,
  text text NOT NULL,
  claim_type text NOT NULL CHECK (claim_type IN ('LEGAL_PROPOSITION','RECORD_FACT','PROCEDURAL','STRATEGIC_OPINION')),
  support jsonb NOT NULL,
  contrary jsonb NOT NULL DEFAULT '[]',
  confidence real,
  depends_on_claim_ids text[] NOT NULL DEFAULT '{}',
  issue_ids text[] NOT NULL DEFAULT '{}',
  origin_role text,
  revision_of text,
  strength text,
  assumptions text[],
  PRIMARY KEY (tenant_id, claim_id),
  CHECK (claim_type = 'STRATEGIC_OPINION' OR jsonb_array_length(support) > 0)
);

ALTER TABLE tpl.claim ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.claim FORCE ROW LEVEL SECURITY;

CREATE POLICY claim_tenant_isolation ON tpl.claim
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

-- 3. Grants
GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.claim TO app_rw, worker, admin_rw;

-- 4. Seed ModelTaskContract for Q&A synthesis
INSERT INTO ops.model_task_contract (
  task_id, owner_phase, input_schema, output_schema, max_input_chars, max_output_tokens,
  data_class_max, allowed_trust_labels, tools_allowed, eval, batch_ok, determinism, prompt_variants
) VALUES (
  'p6.qa_synthesis@1',
  'P6',
  '{
    "type": "object",
    "required": ["question", "evidence_chunks"],
    "properties": {
      "question": {"type": "string"},
      "as_of_legal_date": {"type": "string"},
      "evidence_chunks": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["item_id", "anchor_id", "work_id", "text"],
          "properties": {
            "item_id": {"type": "string"},
            "anchor_id": {"type": "string"},
            "work_id": {"type": "string"},
            "court_id": {"type": ["string", "null"]},
            "title": {"type": ["string", "null"]},
            "text": {"type": "string"}
          }
        }
      }
    }
  }'::jsonb,
  '{
    "type": "object",
    "required": ["summary", "claims", "in_corpus", "contrary_sweep"],
    "properties": {
      "summary": {"type": "string"},
      "in_corpus": {"type": "boolean"},
      "claims": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["text", "claim_type", "anchor_id", "quote", "support_type"],
          "properties": {
            "text": {"type": "string"},
            "claim_type": {
              "type": "string",
              "enum": ["LEGAL_PROPOSITION", "RECORD_FACT", "PROCEDURAL", "STRATEGIC_OPINION"]
            },
            "anchor_id": {"type": "string"},
            "quote": {"type": "string"},
            "support_type": {"type": "string", "enum": ["DIRECT", "INFERENCE"]}
          }
        }
      },
      "contrary_sweep": {
        "type": "object",
        "required": ["status", "notes"],
        "properties": {
          "status": {"type": "string"},
          "notes": {"type": "string"}
        }
      }
    }
  }'::jsonb,
  50000,
  4096,
  'PRIVILEGED',
  ARRAY['PUBLIC_PRIMARY', 'CANONICAL', 'PRIMARY'],
  ARRAY[]::text[],
  '{"metric": "claim_grounding", "gold_set": "g_qa_v1"}'::jsonb,
  false,
  '{"temperature": 0.0}'::jsonb,
  '{"default": "You are a corporate law assistant. Answer the legal question based ONLY on the provided evidence chunks.\\n\\n{inputs}"}'::jsonb
) ON CONFLICT (task_id) DO UPDATE SET
  input_schema = EXCLUDED.input_schema,
  output_schema = EXCLUDED.output_schema,
  max_input_chars = EXCLUDED.max_input_chars,
  max_output_tokens = EXCLUDED.max_output_tokens;

-- 5. Seed ModelEndpoints qualified for p6.qa_synthesis@1
INSERT INTO ops.model_endpoint (
  endpoint_id, provider, model_id, model_snapshot, processing_geo, storage_geo,
  zdr, data_class_max, price, limits, health, qualified_tasks
) VALUES
(
  'ep_fake_qa', 'fake', 'fake-qa-v1', '2026-10-01', 'IN', 'IN',
  true, 'PRIVILEGED', '{"in_per_mtok": 0.0, "out_per_mtok": 0.0}'::jsonb,
  '{"concurrency": 100}'::jsonb, 'UP', '{"p6.qa_synthesis@1": true}'::jsonb
),
(
  'ep_claude_sonnet_3_5', 'anthropic', 'claude-3-5-sonnet-20241022', 'claude-3-5-sonnet-20241022', 'US', 'US',
  true, 'PRIVILEGED', '{"in_per_mtok": 3.0, "out_per_mtok": 15.0}'::jsonb,
  '{"concurrency": 20}'::jsonb, 'UP', '{"p6.qa_synthesis@1": true}'::jsonb
)
ON CONFLICT (endpoint_id) DO UPDATE SET
  health = 'UP',
  qualified_tasks = ops.model_endpoint.qualified_tasks || '{"p6.qa_synthesis@1": true}'::jsonb;
"""

SQL_REVERSE = """
DELETE FROM ops.model_endpoint WHERE endpoint_id IN ('ep_fake_qa', 'ep_claude_sonnet_3_5');
DELETE FROM ops.model_task_contract WHERE task_id = 'p6.qa_synthesis@1';
DROP TABLE IF EXISTS tpl.claim CASCADE;
DELETE FROM ops.pipeline_version WHERE pipeline_version = 'p6.reasoner@0.1.0|qa_synthesis_v1';
"""


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("retrieve", "0001_initial_retrieve_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
