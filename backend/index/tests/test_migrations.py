"""Tests for index application migrations: reversible rollbacks to zero and forward application.

Normative sources:
- AGENTS.md §5: Migrations are reversible, one per logical change
- Session S06 exit check: migrate index zero --database=owner, then migrate forward again
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from django.core.management import call_command
from django.db import connection

pytestmark = pytest.mark.django_db(databases=["default", "owner"], transaction=True)


@pytest.fixture(autouse=True)
def ensure_migrated_state() -> Generator[None]:
    """Ensure database is at latest migration forward before and after the test."""
    yield
    call_command("migrate", "index", database="owner")


def _table_exists(schema: str, table: str) -> bool:
    """Check if a table exists in postgres."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s;
            """,
            [schema, table],
        )
        return cur.fetchone() is not None


def _ts_config_exists(name: str) -> bool:
    """Check if a text search configuration exists in public schema."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM pg_ts_config c
            JOIN pg_namespace n ON n.oid = c.cfgnamespace
            WHERE n.nspname = 'public' AND c.cfgname = %s;
            """,
            [name],
        )
        return cur.fetchone() is not None


def test_migrations_rollback_to_zero_and_forward() -> None:
    """Test that migrating index to zero cleanly drops all artifacts, and migrating forward rebuilds them."""
    # 1. Migrate index to zero
    call_command("migrate", "index", "zero", database="owner")

    # Assert that index tables are dropped
    assert not _table_exists("plc", "chunk")
    assert not _table_exists("plc", "chunk_g1")
    assert not _table_exists("plc", "index_expression_state")
    assert not _table_exists("plc", "summary")
    assert not _table_exists("tpl", "private_chunk")
    assert not _table_exists("ops", "index_generation")
    assert not _table_exists("ops", "index_alias")
    assert not _ts_config_exists("legal_en")

    # 2. Migrate index forward to latest
    call_command("migrate", "index", database="owner")

    # Assert that text search configuration exists
    assert _ts_config_exists("legal_en")

    # Assert that all tables exist
    assert _table_exists("ops", "index_generation")
    assert _table_exists("ops", "index_alias")
    assert _table_exists("plc", "chunk")
    assert _table_exists("plc", "chunk_g1")
    assert _table_exists("plc", "index_expression_state")
    assert _table_exists("plc", "summary")
    assert _table_exists("tpl", "private_chunk")

    # Assert that g1 partition indexes exist
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT indexname FROM pg_indexes
            WHERE schemaname = 'plc' AND tablename = 'chunk_g1';
            """
        )
        indexes = {r[0] for r in cur.fetchall()}

    assert "chunk_g1_embedding_hnsw" in indexes
    assert "chunk_g1_tsv_gin" in indexes
    assert "chunk_g1_binding_tags_gin" in indexes
    assert "chunk_g1_work_id_idx" in indexes

    # Assert that seeded pipeline versions exist
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT pipeline_version FROM ops.pipeline_version
            WHERE component IN ('p2.chunker', 'p2.embedder', 'p2.index');
            """
        )
        p_vers = {r[0] for r in cur.fetchall()}

    assert "p2.chunker@0.1.0|det_v1" in p_vers
    assert "p2.embedder@0.1.0|approx_tok_v1|voyage-4-large|1024" in p_vers
    assert "p2.index@0.1.0|g1" in p_vers

    # Assert that voyage endpoint exists with US geo
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT processing_geo, storage_geo FROM ops.model_endpoint
            WHERE endpoint_id = 'ep_voyage_4_large';
            """
        )
        row = cur.fetchone()
        assert row is not None
        assert row[0] == "US"
        assert row[1] == "US"

    # Assert deduplicated subscriptions (exactly 3 rows for index_pipeline)
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT type FROM ops.event_subscription
            WHERE consumer = 'index_pipeline';
            """
        )
        sub_types = {r[0] for r in cur.fetchall()}

    assert sub_types == {"doc.parsed.v1", "identity.merged.v1", "identity.split.v1"}
