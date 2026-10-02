"""Tests for Migration 0002 and schema contracts.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.3
- S05b Directives:
  - plc.citation_mention exists with required fields
  - plc.identity_merge_ledger exists with required fields
  - Zero new SQL tables for statute mentions (mvp/03 line 321)
  - Permissions and grants on public corpus tables
"""

import pytest
from django.db import connection


@pytest.mark.django_db
def test_migration_0002_tables_and_columns() -> None:
    with connection.cursor() as cursor:
        # Check plc.citation_mention columns
        cursor.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'plc' AND table_name = 'citation_mention'
            ORDER BY ordinal_position;
            """
        )
        cm_cols = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
        assert "mention_id" in cm_cols
        assert "citing_work_id" in cm_cols
        assert "anchor_id" in cm_cols
        assert "raw_text" in cm_cols
        assert "mention_kind" in cm_cols
        assert "scheme" in cm_cols
        assert "normalized" in cm_cols
        assert "resolved_target_id" in cm_cols
        assert "resolution_confidence" in cm_cols
        assert "resolution_method" in cm_cols
        assert "temporal_check" in cm_cols

        # Check plc.identity_merge_ledger columns
        cursor.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'plc' AND table_name = 'identity_merge_ledger'
            ORDER BY ordinal_position;
            """
        )
        iml_cols = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
        assert "event_id" in iml_cols
        assert "kind" in iml_cols
        assert "op" in iml_cols
        assert "from_id" in iml_cols
        assert "to_id" in iml_cols
        assert "reason" in iml_cols
        assert "confidence" in iml_cols
        assert "recorded_at" in iml_cols


@pytest.mark.django_db
def test_zero_new_tables_for_statute_mentions() -> None:
    # Directive #5: Statute mentions live only inside ParsedDocument. Zero new SQL tables for statute mentions.
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'plc' AND table_name LIKE '%statute%';
            """
        )
        rows = cursor.fetchall()
        assert len(rows) == 0, f"Expected 0 statute tables in plc, found: {rows}"
