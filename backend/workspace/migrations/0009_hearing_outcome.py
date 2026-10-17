"""Add outcome column to tpl.hearing.

Normative source:
- Session R2: "After a hearing happens: record what happened (status: heard, adjourned, not reached, cancelled)"
"""

from __future__ import annotations

from django.db import migrations

SQL_FORWARD = """
ALTER TABLE tpl.hearing ADD COLUMN IF NOT EXISTS outcome text;
"""

SQL_REVERSE = """
ALTER TABLE tpl.hearing DROP COLUMN IF EXISTS outcome;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0008_backfill_case_links_normalization"),
    ]

    operations = [
        migrations.RunSQL(SQL_FORWARD, SQL_REVERSE),
    ]
