"""Qualify Gemini endpoint for p6.qa_synthesis@1 and deactivate retired endpoints.

DECISIONS.md: Gemini temporarily primary for Q&A synthesis until Anthropic key is available;
04 §194 primary is Claude Sonnet 5.5.
"""

from __future__ import annotations

from django.db import migrations

SQL_FORWARD = """
-- 1. Register and qualify Gemini 3.8 Flash endpoint for p6.qa_synthesis@1
INSERT INTO ops.model_endpoint (
  endpoint_id, provider, model_id, model_snapshot, processing_geo, storage_geo,
  zdr, data_class_max, price, limits, health, qualified_tasks
) VALUES (
  'ep_gemini_3_8_flash', 'google', 'gemini-3.8-flash', 'gemini-3.8-flash', 'GLOBAL', 'US',
  true, 'PUBLIC', '{"in_per_mtok": 0.75, "out_per_mtok": 3.75}'::jsonb,
  '{"concurrency": 20}'::jsonb, 'UP', '{"p6.qa_synthesis@1": true}'::jsonb
) ON CONFLICT (endpoint_id) DO UPDATE SET
  health = 'UP',
  model_id = 'gemini-3.8-flash',
  model_snapshot = 'gemini-3.8-flash',
  data_class_max = 'PUBLIC',
  price = '{"in_per_mtok": 0.75, "out_per_mtok": 3.75}'::jsonb,
  qualified_tasks = ops.model_endpoint.qualified_tasks || '{"p6.qa_synthesis@1": true}'::jsonb;

-- 2. Deactivate retired ep_claude_sonnet_3_5 and fake endpoint for live execution
UPDATE ops.model_endpoint
SET health = 'DOWN'
WHERE endpoint_id = 'ep_claude_sonnet_3_5';
"""

SQL_REVERSE = """
DELETE FROM ops.model_endpoint WHERE endpoint_id = 'ep_gemini_3_8_flash';
UPDATE ops.model_endpoint SET health = 'UP' WHERE endpoint_id = 'ep_claude_sonnet_3_5';
"""


class Migration(migrations.Migration):
    dependencies = [
        ("reason", "0001_initial_reason_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
