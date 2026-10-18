"""Migration 0012: Add sheet_name column to tpl.import_job.

Normative source: Session R3 Fix Pass - Item 3.
"""

from django.db import migrations

SQL_FORWARD = """
ALTER TABLE tpl.import_job ADD COLUMN IF NOT EXISTS sheet_name text;
"""

SQL_REVERSE = """
ALTER TABLE tpl.import_job DROP COLUMN IF EXISTS sheet_name;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("workspace", "0011_tasks_client_updates_import"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
