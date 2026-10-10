"""Qualify ep_gemini_3_5_flash for p6.qa_synthesis@1 and set endpoint priorities.

Normative source: Session S07 Directive #1:
- Add endpoint ep_gemini_3_5_flash (same data class/price fields, real 3.5 price) qualified for p6.qa_synthesis@1.
- Priority: ep_gemini_3_8_flash (priority 1), ep_gemini_3_5_flash (priority 2).
"""

from __future__ import annotations

from django.db import migrations

SQL_FORWARD = """
-- 1. Ensure ep_gemini_3_8_flash has priority 1
UPDATE ops.model_endpoint
SET limits = jsonb_set(COALESCE(limits, '{}'::jsonb), '{priority}', '1'::jsonb)
WHERE endpoint_id = 'ep_gemini_3_8_flash';

-- 2. Register and qualify Gemini 3.5 Flash endpoint with priority 2 and real 3.5 price
INSERT INTO ops.model_endpoint (
  endpoint_id, provider, model_id, model_snapshot, processing_geo, storage_geo,
  zdr, data_class_max, price, limits, health, qualified_tasks
) VALUES (
  'ep_gemini_3_5_flash', 'google', 'gemini-3.5-flash', 'gemini-3.5-flash', 'GLOBAL', 'US',
  true, 'PUBLIC', '{"in_per_mtok": 0.075, "out_per_mtok": 0.30}'::jsonb,
  '{"concurrency": 20, "priority": 2}'::jsonb, 'UP', '{"p6.qa_synthesis@1": true}'::jsonb
) ON CONFLICT (endpoint_id) DO UPDATE SET
  health = 'UP',
  model_id = 'gemini-3.5-flash',
  model_snapshot = 'gemini-3.5-flash',
  data_class_max = 'PUBLIC',
  price = '{"in_per_mtok": 0.075, "out_per_mtok": 0.30}'::jsonb,
  limits = '{"concurrency": 20, "priority": 2}'::jsonb,
  qualified_tasks = ops.model_endpoint.qualified_tasks || '{"p6.qa_synthesis@1": true}'::jsonb;
"""

SQL_REVERSE = """
DELETE FROM ops.model_endpoint WHERE endpoint_id = 'ep_gemini_3_5_flash';
UPDATE ops.model_endpoint
SET limits = limits - 'priority'
WHERE endpoint_id = 'ep_gemini_3_8_flash';
"""


class Migration(migrations.Migration):
    dependencies = [
        ("reason", "0002_qualify_gemini_qa_endpoint"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
