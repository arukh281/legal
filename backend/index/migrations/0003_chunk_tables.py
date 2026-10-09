"""Migration 0003: plc.chunk partitioned table and plc.chunk_g1 partition.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.5 (plc.chunk DDL and plc.chunk_g1 partition)
- docs/mvp/04_stack_and_infra.md §2.4 (HNSW parameters m=16, ef_construction=64)
"""

from django.db import migrations

SQL_FORWARD = """
CREATE TABLE plc.chunk (
  chunk_id text NOT NULL,
  index_generation text NOT NULL,
  work_id text NOT NULL,
  expression_key text NOT NULL,
  anchor_ids text[] NOT NULL,
  anchor_first text NOT NULL,
  anchor_last text NOT NULL,
  chunk_kind text NOT NULL,
  rhetorical_role text,
  opinion_role text,
  context_header text NOT NULL,
  text text NOT NULL,
  text_hash text NOT NULL,
  court_id text,
  court_level text,
  bench_strength smallint,
  decision_date date,
  doc_type text NOT NULL,
  binding_scope_tags text[] NOT NULL DEFAULT '{}',
  cited_work_ids text[] NOT NULL DEFAULT '{}',
  cited_provision_anchors text[] NOT NULL DEFAULT '{}',
  valid_from date,
  valid_to date,
  in_force boolean,
  trust_label text NOT NULL DEFAULT 'PLC_OFFICIAL',
  rights_class text NOT NULL,
  quality jsonb NOT NULL,
  body jsonb NOT NULL,
  tsv tsvector NOT NULL,
  embedding halfvec NOT NULL,
  doc_seq bigint NOT NULL,
  pipeline_version text NOT NULL REFERENCES ops.pipeline_version,
  PRIMARY KEY (index_generation, chunk_id)
) PARTITION BY LIST (index_generation);

CREATE TABLE plc.chunk_g1 PARTITION OF plc.chunk FOR VALUES IN ('g1');
ALTER TABLE plc.chunk_g1 ALTER COLUMN embedding SET STORAGE PLAIN;
CREATE INDEX chunk_g1_embedding_hnsw ON plc.chunk_g1 USING hnsw ((embedding::halfvec(1024)) halfvec_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX chunk_g1_tsv_gin ON plc.chunk_g1 USING gin (tsv);
CREATE INDEX chunk_g1_binding_tags_gin ON plc.chunk_g1 USING gin (binding_scope_tags);
CREATE INDEX chunk_g1_work_id_idx ON plc.chunk_g1 (work_id);
"""

SQL_REVERSE = """
DROP TABLE IF EXISTS plc.chunk_g1 CASCADE;
DROP TABLE IF EXISTS plc.chunk CASCADE;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("index", "0002_ops_index_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
