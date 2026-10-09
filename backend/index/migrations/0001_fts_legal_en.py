"""Migration 0001: Custom legal English text search configuration (public.legal_en).

Normative sources:
- docs/mvp/04_stack_and_infra.md §2.3 (custom text-search configuration legal_en)
- Session S06 Directive #1: Schema-qualified public.legal_en everywhere
"""

from django.db import migrations

SQL_FORWARD = """
CREATE TEXT SEARCH CONFIGURATION public.legal_en (COPY = english);
"""

SQL_REVERSE = """
DROP TEXT SEARCH CONFIGURATION IF EXISTS public.legal_en CASCADE;
"""


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("ops", "0001_initial_extensions_and_schemas"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
