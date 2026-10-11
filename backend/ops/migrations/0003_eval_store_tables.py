"""Migration 0003: Evaluation store tables (ops.gold_set, ops.eval_case, ops.eval_run, ops.eval_result).

Verbatim DDL and contracts from:
- docs/mvp/03_data_model_and_contracts.md §1, §3.15
- docs/mvp/06_test_set_plan.md §7
- docs/01_master_architecture.md §5.2
"""

from django.db import migrations

SQL_FORWARD = """
CREATE TABLE ops.gold_set (
  gold_set_id text PRIMARY KEY,
  name text NOT NULL,
  version int NOT NULL DEFAULT 1,
  frozen_at timestamptz,
  scope text NOT NULL CHECK (scope IN ('TENANT_PRIVATE','PUBLIC')),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ops.eval_case (
  eval_case_id text PRIMARY KEY,
  gold_set_id text NOT NULL REFERENCES ops.gold_set(gold_set_id) ON DELETE CASCADE,
  version int NOT NULL,
  split text NOT NULL CHECK (split IN ('DEV','EXAM','TRAIN')),
  task text NOT NULL,
  strata jsonb NOT NULL,
  input jsonb NOT NULL,
  expected jsonb NOT NULL,
  provenance jsonb NOT NULL,
  depends_on_ids text[] NOT NULL DEFAULT '{}',
  stale boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX eval_case_gold_set_idx ON ops.eval_case(gold_set_id, split);

CREATE TABLE ops.eval_run (
  run_id text PRIMARY KEY,
  gold_set_id text NOT NULL REFERENCES ops.gold_set(gold_set_id) ON DELETE RESTRICT,
  candidate jsonb NOT NULL,
  metrics jsonb NOT NULL,
  gate_decision text NOT NULL CHECK (gate_decision IN ('PROMOTE','REJECT','WAIVED','PREVIEW')),
  sentinel_failures jsonb,
  cost_usd numeric(10,6),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ops.eval_result (
  result_id text PRIMARY KEY,
  run_id text NOT NULL REFERENCES ops.eval_run(run_id) ON DELETE CASCADE,
  eval_case_id text NOT NULL REFERENCES ops.eval_case(eval_case_id) ON DELETE RESTRICT,
  actual jsonb NOT NULL,
  passed boolean NOT NULL,
  score numeric(6,4),
  reasons text[] NOT NULL DEFAULT '{}',
  gate_checks jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX eval_result_run_idx ON ops.eval_result(run_id);
"""

SQL_REVERSE = """
DROP TABLE IF EXISTS ops.eval_result;
DROP TABLE IF EXISTS ops.eval_run;
DROP TABLE IF EXISTS ops.eval_case;
DROP TABLE IF EXISTS ops.gold_set;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("ops", "0002_initial_ops_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
