"""Migration 0009: Fix Voyage model endpoint geo and deduplicate index event subscriptions.

Normative sources:
- Session S06 Step 1.2: Set processing_geo and storage_geo to US for ep_voyage_4_large.
- Session S06 Step 1.3: Deduplicate index_pipeline subscriptions (remove plc.-prefixed types).
"""

from django.db import migrations

SQL_FORWARD = """
-- Fix Voyage model endpoint geos: Voyage AI processes and stores in US
UPDATE ops.model_endpoint
SET processing_geo = 'US', storage_geo = 'US'
WHERE endpoint_id = 'ep_voyage_4_large';

-- Remove redundant plc.-prefixed event subscriptions
DELETE FROM ops.event_subscription
WHERE consumer = 'index_pipeline' AND type LIKE 'plc.%';
"""

SQL_REVERSE = """
UPDATE ops.model_endpoint
SET processing_geo = 'IN', storage_geo = 'IN'
WHERE endpoint_id = 'ep_voyage_4_large';

INSERT INTO ops.event_subscription (consumer, type, handler, lane, enabled)
VALUES
  ('index_pipeline', 'plc.doc.parsed.v1', 'index.consumer.handle_event', 'bulk', true),
  ('index_pipeline', 'plc.identity.merged.v1', 'index.consumer.handle_event', 'rt', true),
  ('index_pipeline', 'plc.identity.split.v1', 'index.consumer.handle_event', 'rt', true)
ON CONFLICT (consumer, type) DO UPDATE SET handler = EXCLUDED.handler, enabled = true;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("index", "0008_grants"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
