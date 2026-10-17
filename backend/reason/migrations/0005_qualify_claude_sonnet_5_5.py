"""Qualify Claude Sonnet 5.5 as Priority 1 for p6.qa_synthesis@1, with Gemini as fallback.

Normative source:
- 04 §194 primary answer synthesis is Claude Sonnet 5.5 ($2/$10 per 04 §206).
- Gemini endpoints (ep_gemini_3_8_flash, ep_gemini_3_5_flash) are fallbacks (priority 2 and 3).
- Verifier/judge family recorded as Gemini (gemini-3.8-flash) so generator != verifier.
"""

from __future__ import annotations

from django.db import migrations

SQL_FORWARD = """
-- 1. Register and qualify Claude Sonnet 5.5 endpoint with priority 1
INSERT INTO ops.model_endpoint (
  endpoint_id, provider, model_id, model_snapshot, processing_geo, storage_geo,
  zdr, data_class_max, price, limits, health, qualified_tasks
) VALUES (
  'ep_claude_sonnet_5_5', 'anthropic', 'claude-sonnet-5-5', 'claude-sonnet-5-5', 'US', 'US',
  true, 'PRIVILEGED', '{"in_per_mtok": 2.0, "out_per_mtok": 10.0, "cache_read_mult": 0.1}'::jsonb,
  '{"concurrency": 20, "priority": 1}'::jsonb, 'UP', '{"p6.qa_synthesis@1": true}'::jsonb
) ON CONFLICT (endpoint_id) DO UPDATE SET
  health = 'UP',
  model_id = 'claude-sonnet-5-5',
  model_snapshot = 'claude-sonnet-5-5',
  data_class_max = 'PRIVILEGED',
  price = '{"in_per_mtok": 2.0, "out_per_mtok": 10.0, "cache_read_mult": 0.1}'::jsonb,
  limits = '{"concurrency": 20, "priority": 1}'::jsonb,
  qualified_tasks = ops.model_endpoint.qualified_tasks || '{"p6.qa_synthesis@1": true}'::jsonb;

-- 2. Repoint Gemini endpoints to priority 2 and 3 (fallbacks)
UPDATE ops.model_endpoint
SET limits = jsonb_set(COALESCE(limits, '{}'::jsonb), '{priority}', '2'::jsonb)
WHERE endpoint_id = 'ep_gemini_3_8_flash';

UPDATE ops.model_endpoint
SET limits = jsonb_set(COALESCE(limits, '{}'::jsonb), '{priority}', '3'::jsonb)
WHERE endpoint_id = 'ep_gemini_3_5_flash';

-- 3. Deactivate old ep_claude_sonnet_3_5
UPDATE ops.model_endpoint
SET health = 'DOWN'
WHERE endpoint_id = 'ep_claude_sonnet_3_5';

-- 4. Record verifier family as Gemini in ops.pipeline_version
UPDATE ops.pipeline_version
SET model_id = 'gemini-3.8-flash', model_snapshot = 'gemini-3.8-flash'
WHERE pipeline_version = 'p8.verifier@0.1.0|ladder_c0_c2_v1';
"""

SQL_REVERSE = """
DELETE FROM ops.model_endpoint WHERE endpoint_id = 'ep_claude_sonnet_5_5';

UPDATE ops.model_endpoint
SET limits = jsonb_set(COALESCE(limits, '{}'::jsonb), '{priority}', '1'::jsonb)
WHERE endpoint_id = 'ep_gemini_3_8_flash';

UPDATE ops.model_endpoint
SET limits = jsonb_set(COALESCE(limits, '{}'::jsonb), '{priority}', '2'::jsonb)
WHERE endpoint_id = 'ep_gemini_3_5_flash';

UPDATE ops.pipeline_version
SET model_id = NULL, model_snapshot = NULL
WHERE pipeline_version = 'p8.verifier@0.1.0|ladder_c0_c2_v1';
"""


class Migration(migrations.Migration):
    dependencies = [
        ("reason", "0004_update_qa_synthesis_prompt"),
        ("verify", "0001_initial_verify_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
