"""Migration 0004: Update ops.eval_case split check constraint to ('DEV', 'EXAM', 'SENTINEL').

Normative reference:
- docs/01_master_architecture.md line 1317: split: 'DEV' | 'EXAM' | 'SENTINEL'
"""

from django.db import migrations

SQL_FORWARD = """
ALTER TABLE ops.eval_case DROP CONSTRAINT eval_case_split_check;
ALTER TABLE ops.eval_case ADD CONSTRAINT eval_case_split_check CHECK (split IN ('DEV', 'EXAM', 'SENTINEL'));
"""

SQL_BACKWARD = """
ALTER TABLE ops.eval_case DROP CONSTRAINT eval_case_split_check;
ALTER TABLE ops.eval_case ADD CONSTRAINT eval_case_split_check CHECK (split IN ('DEV', 'EXAM', 'TRAIN'));
"""


class Migration(migrations.Migration):
    dependencies = [
        ("ops", "0003_eval_store_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_BACKWARD,
        ),
    ]
