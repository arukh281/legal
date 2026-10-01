"""Migration 0001: extensions and schemas (03 §1 line 68-69)."""

from django.db import migrations

SQL_FORWARD = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE SCHEMA IF NOT EXISTS plc;
CREATE SCHEMA IF NOT EXISTS tpl;
CREATE SCHEMA IF NOT EXISTS ops;
"""

SQL_REVERSE = """
DROP SCHEMA IF EXISTS ops CASCADE;
DROP SCHEMA IF EXISTS tpl CASCADE;
DROP SCHEMA IF EXISTS plc CASCADE;

DROP EXTENSION IF EXISTS unaccent;
DROP EXTENSION IF EXISTS pg_trgm;
DROP EXTENSION IF EXISTS btree_gist;
DROP EXTENSION IF EXISTS vector;
"""


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
