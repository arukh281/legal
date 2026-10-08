"""Migration 0003: Add details jsonb column to plc.identity_merge_ledger.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.3
- S05b Follow-up directive (details jsonb on identity_merge_ledger)
"""

from __future__ import annotations

from django.db import migrations

UP_SQL = """
ALTER TABLE plc.identity_merge_ledger ADD COLUMN IF NOT EXISTS details jsonb;
"""

DOWN_SQL = """
ALTER TABLE plc.identity_merge_ledger DROP COLUMN IF EXISTS details;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("parse", "0002_citation_and_merge_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=UP_SQL,
            reverse_sql=DOWN_SQL,
        ),
    ]
