"""Data migration to normalize existing matter_case_link values using anchor_lib.case_numbers.

Normative source:
- Session R2 Correction 4: Run new normalizer on write, backfill existing rows in a reversible data migration.
"""

from __future__ import annotations

from typing import Any

from django.db import migrations


def backfill_case_links(apps: Any, schema_editor: Any) -> None:
    from anchor_lib.case_numbers import normalize_case_number

    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tenant_id, matter_id, scheme, value_normalized FROM tpl.matter_case_link"
        )
        rows = cursor.fetchall()

        for tenant_id, matter_id, scheme, val in rows:
            parsed = normalize_case_number(val)
            if parsed.parseable and parsed.canonical != val:
                # Update to canonical format if no conflict
                cursor.execute(
                    """
                    UPDATE tpl.matter_case_link
                    SET value_normalized = %s
                    WHERE tenant_id = %s AND matter_id = %s AND scheme = %s AND value_normalized = %s
                    AND NOT EXISTS (
                        SELECT 1 FROM tpl.matter_case_link
                        WHERE tenant_id = %s AND matter_id = %s AND scheme = %s AND value_normalized = %s
                    )
                    """,
                    [parsed.canonical, tenant_id, matter_id, scheme, val, tenant_id, matter_id, scheme, parsed.canonical],
                )


def reverse_backfill(apps: Any, schema_editor: Any) -> None:
    # Canonical forms remain valid normalized representations
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0007_can_read_matter_system_actor"),
    ]

    operations = [
        migrations.RunPython(backfill_case_links, reverse_backfill),
    ]
