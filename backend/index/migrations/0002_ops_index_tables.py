"""Migration 0002: ops.index_generation and ops.index_alias tables.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.5 (index generations and aliases)
"""

from django.db import migrations

SQL_FORWARD = """
CREATE TABLE ops.index_generation (
  index_family text NOT NULL CHECK (index_family IN ('plc_chunks','tpl_chunks')),
  generation text NOT NULL,
  chunker_version text NOT NULL REFERENCES ops.pipeline_version,
  embed_model text NOT NULL,
  embed_dims int NOT NULL,
  fts_config text NOT NULL,
  state text NOT NULL CHECK (state IN ('BUILDING','SHADOW','LIVE','RETIRED','ROLLED_BACK')),
  eval_report_uri text,
  gate_decision_id text,
  created_at timestamptz NOT NULL,
  promoted_at timestamptz,
  rollback_deadline timestamptz,
  PRIMARY KEY (index_family, generation)
);

CREATE TABLE ops.index_alias (
  index_family text PRIMARY KEY,
  generation text NOT NULL,
  previous_generation text,
  swapped_at timestamptz NOT NULL,
  FOREIGN KEY (index_family, generation) REFERENCES ops.index_generation
);
"""

SQL_REVERSE = """
DROP TABLE IF EXISTS ops.index_alias CASCADE;
DROP TABLE IF EXISTS ops.index_generation CASCADE;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("index", "0001_fts_legal_en"),
        ("ops", "0002_initial_ops_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
