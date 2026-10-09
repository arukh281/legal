"""Migration 0007: Seed pipeline versions, provisional index generations, and event subscriptions.

Normative sources:
- Session S06 Directive #8: g1 is seeded in state BUILDING without an alias row.
- Session S06 Directive #9: Seed ('tpl_chunks', 'g1') generation row as well.
- Session S06 Directive #11: Seed event subscriptions for index consumer.
"""

from django.db import migrations

SQL_FORWARD = """
-- Pipeline versions
INSERT INTO ops.pipeline_version (
  pipeline_version, component, semver, model_id, model_snapshot, endpoint_region, prompt_hash, code_sha, created_at
) VALUES
  ('p2.chunker@0.1.0|det_v1', 'p2.chunker', '0.1.0', NULL, NULL, NULL, NULL, 'git-s06', now()),
  ('p2.embedder@0.1.0|approx_tok_v1|voyage-4-large|1024', 'p2.embedder', '0.1.0', 'voyage-4-large', '2026-01-01', 'IN', NULL, 'git-s06', now()),
  ('p2.index@0.1.0|g1', 'p2.index', '0.1.0', 'voyage-4-large', '2026-01-01', 'IN', NULL, 'git-s06', now())
ON CONFLICT (pipeline_version) DO NOTHING;

-- Provisional index generations in state BUILDING (Directive #8 & #9: NO alias row yet)
INSERT INTO ops.index_generation (
  index_family, generation, chunker_version, embed_model, embed_dims, fts_config, state, created_at
) VALUES
  ('plc_chunks', 'g1', 'p2.chunker@0.1.0|det_v1', 'voyage-4-large', 1024, 'public.legal_en', 'BUILDING', now()),
  ('tpl_chunks', 'g1', 'p2.chunker@0.1.0|det_v1', 'voyage-4-large', 1024, 'public.legal_en', 'BUILDING', now())
ON CONFLICT (index_family, generation) DO NOTHING;

-- Event subscriptions for index consumer (Directive #11)
INSERT INTO ops.event_subscription (consumer, type, handler, lane, enabled)
VALUES
  ('index_pipeline', 'doc.parsed.v1', 'index.consumer.handle_event', 'bulk', true),
  ('index_pipeline', 'identity.merged.v1', 'index.consumer.handle_event', 'rt', true),
  ('index_pipeline', 'identity.split.v1', 'index.consumer.handle_event', 'rt', true),
  ('index_pipeline', 'plc.doc.parsed.v1', 'index.consumer.handle_event', 'bulk', true),
  ('index_pipeline', 'plc.identity.merged.v1', 'index.consumer.handle_event', 'rt', true),
  ('index_pipeline', 'plc.identity.split.v1', 'index.consumer.handle_event', 'rt', true)
ON CONFLICT (consumer, type) DO UPDATE SET handler = EXCLUDED.handler, enabled = true;

-- Model Endpoint for voyage-4-large embedding
INSERT INTO ops.model_endpoint (
  endpoint_id, provider, model_id, model_snapshot, processing_geo, storage_geo,
  zdr, data_class_max, price, limits, health, qualified_tasks
) VALUES (
  'ep_voyage_4_large', 'voyage', 'voyage-4-large', '2026-01-01', 'IN', 'IN',
  true, 'PRIVILEGED', '{"in_per_mtok": 0.12, "out_per_mtok": 0.0}'::jsonb,
  '{"concurrency": 20}'::jsonb, 'UP', '{"p2.embed.v1": true}'::jsonb
)
ON CONFLICT (endpoint_id) DO NOTHING;
"""

SQL_REVERSE = """
DELETE FROM plc.chunk;
DELETE FROM tpl.private_chunk;
DELETE FROM plc.summary;
DELETE FROM plc.index_expression_state;
DELETE FROM ops.model_endpoint WHERE endpoint_id = 'ep_voyage_4_large';
DELETE FROM ops.event_subscription WHERE consumer = 'index_pipeline';
DELETE FROM ops.index_alias WHERE generation = 'g1';
DELETE FROM ops.index_generation WHERE generation = 'g1';
DELETE FROM ops.pipeline_version WHERE pipeline_version IN (
  'p2.chunker@0.1.0|det_v1',
  'p2.embedder@0.1.0|approx_tok_v1|voyage-4-large|1024',
  'p2.index@0.1.0|g1'
);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("index", "0006_private_chunk"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
