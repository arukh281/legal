"""Migration 0008: Database role permissions for index tables.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §1 item 1 (role boundaries)
- Session S06 Directive #9: plc_writer gets no grants on tpl.private_chunk.
"""

from django.db import migrations

SQL_FORWARD = """
-- Ops index tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ops.index_generation, ops.index_alias TO app_rw, worker, plc_writer, admin_rw;

-- PLC index tables
GRANT SELECT, INSERT, UPDATE, DELETE ON plc.chunk, plc.chunk_g1, plc.index_expression_state, plc.summary TO app_rw, worker, plc_writer, admin_rw;

-- TPL private chunk (plc_writer explicitly excluded per 03 §1 and Directive #9)
GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.private_chunk TO app_rw, worker, admin_rw;
"""

SQL_REVERSE = """
REVOKE ALL ON tpl.private_chunk FROM app_rw, worker, admin_rw;
REVOKE ALL ON plc.chunk, plc.chunk_g1, plc.index_expression_state, plc.summary FROM app_rw, worker, plc_writer, admin_rw;
REVOKE ALL ON ops.index_generation, ops.index_alias FROM app_rw, worker, plc_writer, admin_rw;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("index", "0007_seed_index_records"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
