"""Migration 0004: plc.index_expression_state table.

Normative sources:
- docs/04_P2_enrichment_indexing.md §2.7 (expression_state schema)
- Session S06 Directives #5, #6: Monotonic re-parse, state tracking, quarantine tracking
"""

from django.db import migrations

SQL_FORWARD = """
CREATE TABLE plc.index_expression_state (
  serial_key text PRIMARY KEY,
  accepted_parse_id text,
  doc_seq bigint NOT NULL DEFAULT 1,
  content_digest bytea,
  enrichment_level text NOT NULL CHECK (enrichment_level IN ('NONE','BASE','FULL')),
  status text NOT NULL CHECK (status IN ('ACTIVE','QUARANTINED','SUPERSEDED_REV','REKEYED')),
  last_quarantined_parse_id text,
  quarantine_reasons jsonb,
  pipeline_version text NOT NULL REFERENCES ops.pipeline_version,
  updated_at timestamptz NOT NULL DEFAULT now()
);
"""

SQL_REVERSE = """
DROP TABLE IF EXISTS plc.index_expression_state CASCADE;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("index", "0003_chunk_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
