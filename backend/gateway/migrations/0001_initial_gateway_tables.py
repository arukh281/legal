"""Migration 0001: Initial Model Gateway tables from 03 §3.15."""

from django.db import migrations

SQL_FORWARD = """
CREATE TABLE ops.model_task_contract (
  task_id text PRIMARY KEY,
  owner_phase text NOT NULL,
  input_schema jsonb NOT NULL,
  output_schema jsonb NOT NULL,
  max_input_chars int NOT NULL,
  max_output_tokens int NOT NULL,
  data_class_max text NOT NULL CHECK (data_class_max IN ('PUBLIC','TENANT_CONFIDENTIAL','PRIVILEGED')),
  allowed_trust_labels text[] NOT NULL,
  tools_allowed text[] NOT NULL DEFAULT '{}',
  eval jsonb NOT NULL,
  latency_slo_ms jsonb,
  batch_ok boolean NOT NULL,
  determinism jsonb NOT NULL,
  escalation jsonb,
  prompt_variants jsonb NOT NULL
);

CREATE TABLE ops.model_endpoint (
  endpoint_id text PRIMARY KEY,
  provider text NOT NULL,
  model_id text NOT NULL,
  model_snapshot text NOT NULL,
  processing_geo text NOT NULL CHECK (processing_geo IN ('IN','APAC','US','GLOBAL','EU')),
  storage_geo text,
  zdr boolean NOT NULL,
  data_class_max text NOT NULL,
  price jsonb NOT NULL,
  limits jsonb NOT NULL,
  health text NOT NULL DEFAULT 'UP',
  qualified_tasks jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE ops.llm_call_record (
  call_id text NOT NULL,
  trace_id text NOT NULL,
  task_id text NOT NULL,
  endpoint_id text NOT NULL,
  pipeline_version text NOT NULL,
  tenant_id text,
  matter_id text,
  dataclass text NOT NULL,
  residency text NOT NULL,
  processing_geo text NOT NULL,
  purpose text,
  input_chars int NOT NULL,
  output_chars int NOT NULL,
  tokens_in int NOT NULL,
  tokens_out int NOT NULL,
  cache_read_tokens int NOT NULL DEFAULT 0,
  usd numeric(10,6) NOT NULL,
  latency_ms int NOT NULL,
  schema_valid boolean NOT NULL,
  repaired boolean NOT NULL,
  escalated_from text,
  inputs_ref text NOT NULL,
  outputs_ref text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (call_id, created_at)
) PARTITION BY RANGE (created_at);

-- Default partition ensures writes succeed across all date ranges
CREATE TABLE ops.llm_call_record_default PARTITION OF ops.llm_call_record DEFAULT;

-- Grants for runtime roles
GRANT SELECT, INSERT, UPDATE, DELETE ON ops.model_task_contract, ops.model_endpoint, ops.llm_call_record, ops.llm_call_record_default TO app_rw, worker;
"""

SQL_REVERSE = """
DROP TABLE IF EXISTS ops.llm_call_record_default CASCADE;
DROP TABLE IF EXISTS ops.llm_call_record CASCADE;
DROP TABLE IF EXISTS ops.model_endpoint CASCADE;
DROP TABLE IF EXISTS ops.model_task_contract CASCADE;
"""


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("ops", "0002_initial_ops_tables"),
        ("workspace", "0002_db_roles_and_rls"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
