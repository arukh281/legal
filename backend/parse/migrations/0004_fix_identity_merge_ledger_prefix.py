"""Migration to fix identity_merge_ledger event_id prefix collision.

Replaces erroneous 'evr_' prefixes in plc.identity_merge_ledger with 'iml_'
so that 'evr_' is reclaimed strictly for EvalRun (P8) per docs/01 §5.2.

Normative sources:
- Session S08 Amendment 2(f)
- docs/01_master_architecture.md §5.2
- docs/mvp/03_data_model_and_contracts.md §1 & §3.15
"""

from django.db import migrations

SQL_FORWARD = """
UPDATE plc.identity_merge_ledger
SET event_id = 'iml_' || SUBSTRING(event_id FROM 5)
WHERE event_id LIKE 'evr_%';
"""

SQL_REVERSE = """
UPDATE plc.identity_merge_ledger
SET event_id = 'evr_' || SUBSTRING(event_id FROM 5)
WHERE event_id LIKE 'iml_%';
"""


class Migration(migrations.Migration):
    dependencies = [
        ("parse", "0003_identity_merge_ledger_details"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
