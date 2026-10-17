"""Migration 0010: Register Gemini embedding endpoint, pipeline versions, and partition plc.chunk_g2.

Normative source:
- Item 5 of S09 preparation session:
  - Build generation g2 with the current Gemini embedding model (gemini-embedding-001, public corpus only).
  - Keep g1 as active alias until evaluation comparison confirms g2 superiority.
"""

from __future__ import annotations

from django.db import migrations

SQL_FORWARD = """
-- 1. Register Gemini embedding endpoint
INSERT INTO ops.model_endpoint (
  endpoint_id, provider, model_id, model_snapshot, processing_geo, storage_geo,
  zdr, data_class_max, price, limits, health, qualified_tasks
) VALUES (
  'ep_gemini_embedding', 'google', 'gemini-embedding-001', 'gemini-embedding-001', 'GLOBAL', 'US',
  true, 'PUBLIC', '{"in_per_mtok": 0.08, "out_per_mtok": 0.0}'::jsonb,
  '{"concurrency": 20}'::jsonb, 'UP', '{"p2.embed.v1": true}'::jsonb
) ON CONFLICT (endpoint_id) DO UPDATE SET
  health = 'UP',
  model_id = 'gemini-embedding-001',
  model_snapshot = 'gemini-embedding-001',
  qualified_tasks = ops.model_endpoint.qualified_tasks || '{"p2.embed.v1": true}'::jsonb;

-- 2. Register pipeline versions for g2
INSERT INTO ops.pipeline_version (
  pipeline_version, component, semver, model_id, model_snapshot, endpoint_region, prompt_hash, code_sha, created_at
) VALUES
  ('p2.embedder@0.1.0|approx_tok_v1|gemini-embedding-001|1024', 'p2.embedder', '0.1.0', 'gemini-embedding-001', 'gemini-embedding-001', 'GLOBAL', NULL, 'git-s09-step5', now()),
  ('p2.index@0.1.0|g2', 'p2.index', '0.1.0', 'gemini-embedding-001', 'gemini-embedding-001', 'GLOBAL', NULL, 'git-s09-step5', now())
ON CONFLICT (pipeline_version) DO NOTHING;

-- 3. Register generation g2 in ops.index_generation
INSERT INTO ops.index_generation (
  index_family, generation, chunker_version, embed_model, embed_dims, fts_config, state, created_at
) VALUES (
  'plc_chunks', 'g2', 'p2.chunker@0.1.0|det_v1', 'gemini-embedding-001', 1024, 'public.legal_en', 'BUILDING', now()
) ON CONFLICT (index_family, generation) DO NOTHING;

-- 4. Create plc.chunk_g2 partition table and indexes
CREATE TABLE IF NOT EXISTS plc.chunk_g2 PARTITION OF plc.chunk FOR VALUES IN ('g2');
ALTER TABLE plc.chunk_g2 ALTER COLUMN embedding SET STORAGE PLAIN;
CREATE INDEX IF NOT EXISTS chunk_g2_embedding_hnsw ON plc.chunk_g2 USING hnsw ((embedding::halfvec(1024)) halfvec_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS chunk_g2_tsv_gin ON plc.chunk_g2 USING gin (tsv);
CREATE INDEX IF NOT EXISTS chunk_g2_binding_tags_gin ON plc.chunk_g2 USING gin (binding_scope_tags);
CREATE INDEX IF NOT EXISTS chunk_g2_work_id_idx ON plc.chunk_g2 (work_id);

-- 5. Permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON plc.chunk_g2 TO app_rw, worker, plc_writer, admin_rw;
"""

SQL_REVERSE = """
DROP TABLE IF EXISTS plc.chunk_g2 CASCADE;
DELETE FROM ops.index_generation WHERE index_family = 'plc_chunks' AND generation = 'g2';
DELETE FROM ops.model_endpoint WHERE endpoint_id = 'ep_gemini_embedding';
DELETE FROM ops.pipeline_version WHERE pipeline_version IN (
  'p2.embedder@0.1.0|approx_tok_v1|gemini-embedding-001|1024',
  'p2.index@0.1.0|g2'
);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("index", "0009_fix_voyage_endpoint_and_subscriptions"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
