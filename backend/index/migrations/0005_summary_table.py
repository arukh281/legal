"""Migration 0005: plc.summary table (case cards and digests, non-citable).

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.5 (plc.summary DDL)
- docs/01_master_architecture.md §7.3
"""

from django.db import migrations

SQL_FORWARD = """
CREATE TABLE plc.summary (
  summary_id text PRIMARY KEY,
  work_id text NOT NULL,
  expression_key text NOT NULL,
  level text NOT NULL,
  scope_anchor_ids text[] NOT NULL,
  fields jsonb,
  sentences jsonb NOT NULL,
  review_state text NOT NULL,
  pipeline_version text NOT NULL REFERENCES ops.pipeline_version,
  recorded_at timestamptz NOT NULL
);
"""

SQL_REVERSE = """
DROP TABLE IF EXISTS plc.summary CASCADE;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("index", "0004_expression_state"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
