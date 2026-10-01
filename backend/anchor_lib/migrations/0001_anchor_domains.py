"""Migration 0001: Postgres anchor domains verbatim from 03 §1 item 3."""

from django.db import migrations

SQL_FORWARD = """
-- public_anchor | provision_ref | pit_ref   (coarse; anchor_lib is authoritative)
CREATE DOMAIN public_anchor_ref AS text CHECK (VALUE ~
  '^wrk_[0-9A-HJKMNP-TV-Z]{26}(/[a-z]{2,3}(\\.r[1-9][0-9]*|@[0-9]{4}-[0-9]{2}-[0-9]{2}(~IN(-[A-Z]{2,3})?)?)?)?#[a-z0-9][A-Za-z0-9.\\-]*(@[0-9]{4}-[0-9]{2}-[0-9]{2}(~IN(-[A-Z]{2,3})?)?)?$');

-- private_anchor: pdoc_…/v2[.mt-en|.ht-en]#[att1/]fragment
CREATE DOMAIN private_anchor_ref AS text CHECK (VALUE ~
  '^pdoc_[0-9A-HJKMNP-TV-Z]{26}/v[1-9][0-9]*(\\.(mt|ht)-[a-z]{2,3})?#(att[1-9][0-9]*/)?[A-Za-z0-9.:\\-]+$');

CREATE DOMAIN any_anchor_ref AS text CHECK (VALUE ~ '^(wrk|pdoc)_[0-9A-HJKMNP-TV-Z]{26}[/#]');
"""

SQL_REVERSE = """
DROP DOMAIN IF EXISTS any_anchor_ref CASCADE;
DROP DOMAIN IF EXISTS private_anchor_ref CASCADE;
DROP DOMAIN IF EXISTS public_anchor_ref CASCADE;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("ops", "0001_initial_extensions_and_schemas"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
