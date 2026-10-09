"""Migration 0006: tpl.private_chunk table with Row-Level Security.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.5 (tpl.private_chunk DDL)
- Session S06 Directive #9: RLS policy pattern, index_generation HNSW index
"""

from django.db import migrations

SQL_FORWARD = """
CREATE TABLE tpl.private_chunk (
  tenant_id text NOT NULL,
  matter_id text NOT NULL,
  chunk_id text NOT NULL,
  index_generation text NOT NULL,
  pdoc_id text NOT NULL,
  pver text NOT NULL,
  anchor_ids private_anchor_ref[] NOT NULL,
  text text NOT NULL,
  trust_label text NOT NULL,
  privilege_class text NOT NULL,
  tsv tsvector NOT NULL,
  embedding halfvec NOT NULL,
  pipeline_version text NOT NULL,
  PRIMARY KEY (tenant_id, index_generation, chunk_id)
);

ALTER TABLE tpl.private_chunk ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.private_chunk FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON tpl.private_chunk
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

CREATE INDEX private_chunk_g1_embedding_hnsw ON tpl.private_chunk
  USING hnsw ((embedding::halfvec(1024)) halfvec_cosine_ops)
  WHERE index_generation = 'g1';
"""

SQL_REVERSE = """
DROP TABLE IF EXISTS tpl.private_chunk CASCADE;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("index", "0005_summary_table"),
        ("workspace", "0002_db_roles_and_rls"),
        ("anchor_lib", "0001_anchor_domains"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
