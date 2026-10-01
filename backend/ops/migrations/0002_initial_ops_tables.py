"""Migration 0002: ops tables verbatim from 03 §3.1 and §3.16."""

from django.db import migrations

SQL_FORWARD = """
CREATE TABLE ops.pipeline_version (
  pipeline_version text PRIMARY KEY,
  component text NOT NULL,
  semver text NOT NULL,
  model_id text,
  model_snapshot text,
  endpoint_region text,
  prompt_hash text,
  code_sha text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ops.event_outbox (
  id text NOT NULL,
  specversion text NOT NULL DEFAULT '1.0',
  type text NOT NULL,
  source text NOT NULL,
  time timestamptz NOT NULL,
  subject text,
  datacontenttype text NOT NULL DEFAULT 'application/json',
  dataschema text NOT NULL,
  tenantid text,
  dataclass text NOT NULL CHECK (dataclass IN ('PUBLIC','TENANT_CONFIDENTIAL','PRIVILEGED')),
  traceparent text,
  causationid text,
  idempotencykey text NOT NULL,
  schemaversion text NOT NULL,
  datasig text,
  data jsonb NOT NULL,
  topic text NOT NULL,
  partition_key text NOT NULL,
  lane text CHECK (lane IN ('rt','bulk')),
  created_at timestamptz NOT NULL DEFAULT now(),
  dispatched_at timestamptz,
  PRIMARY KEY (source, id),
  CHECK ((dataclass = 'PUBLIC') = (tenantid IS NULL)),
  CHECK (topic LIKE CASE WHEN tenantid IS NULL THEN 'plc.%' ELSE 'tpl.' || tenantid || '.%' END)
);

CREATE INDEX outbox_pending ON ops.event_outbox (created_at) WHERE dispatched_at IS NULL;

CREATE TABLE ops.event_subscription (
  consumer text,
  type text,
  handler text NOT NULL,
  lane text,
  enabled boolean NOT NULL DEFAULT true,
  PRIMARY KEY (consumer, type)
);

CREATE TABLE ops.event_inbox (
  consumer text NOT NULL,
  idempotencykey text NOT NULL,
  payload_hash bytea NOT NULL,
  event_id text NOT NULL,
  processed_at timestamptz NOT NULL,
  PRIMARY KEY (consumer, idempotencykey)
);

CREATE TABLE ops.event_parked (
  consumer text,
  event_id text,
  reason text NOT NULL,
  parked_at timestamptz NOT NULL,
  PRIMARY KEY (consumer, event_id)
);

CREATE TABLE ops.job_chain (
  job_id text PRIMARY KEY,
  kind text NOT NULL,
  tenant_id text,
  matter_id text,
  idempotency_key text NOT NULL UNIQUE,
  status text NOT NULL CHECK (status IN ('RUNNING','WAITING_HITL','PUBLISHED','FAILED','CANCELLED')),
  request jsonb NOT NULL,
  budget jsonb NOT NULL,
  spent jsonb NOT NULL DEFAULT '{}',
  current_step text,
  context_version bigint,
  as_known_at timestamptz,
  created_at timestamptz NOT NULL,
  finished_at timestamptz
);

CREATE TABLE ops.job_step (
  job_id text REFERENCES ops.job_chain,
  step text NOT NULL,
  attempt int NOT NULL DEFAULT 1,
  status text NOT NULL CHECK (status IN ('PENDING','RUNNING','WAITING','DONE','FAILED','SKIPPED')),
  step_key text NOT NULL,
  input_hashes text[] NOT NULL,
  output jsonb,
  output_ref text,
  pipeline_version text,
  procrastinate_job_id bigint,
  heartbeat_at timestamptz,
  started_at timestamptz,
  finished_at timestamptz,
  error jsonb,
  PRIMARY KEY (job_id, step, attempt)
);

CREATE TABLE ops.job_signal (
  job_id text REFERENCES ops.job_chain,
  signal text NOT NULL CHECK (signal IN ('confirm_dates','confirm_issues','approve_draft','cancel')),
  payload jsonb NOT NULL,
  received_at timestamptz NOT NULL,
  consumed_at timestamptz,
  PRIMARY KEY (job_id, signal, received_at)
);
"""

SQL_REVERSE = """
DROP TABLE IF EXISTS ops.job_signal CASCADE;
DROP TABLE IF EXISTS ops.job_step CASCADE;
DROP TABLE IF EXISTS ops.job_chain CASCADE;
DROP TABLE IF EXISTS ops.event_parked CASCADE;
DROP TABLE IF EXISTS ops.event_inbox CASCADE;
DROP TABLE IF EXISTS ops.event_subscription CASCADE;
DROP TABLE IF EXISTS ops.event_outbox CASCADE;
DROP TABLE IF EXISTS ops.pipeline_version CASCADE;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("ops", "0001_initial_extensions_and_schemas"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
