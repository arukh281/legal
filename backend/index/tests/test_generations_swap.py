"""Tests for index generations, partition creation, atomic alias swap, and rollback.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.5
- docs/04_P2_enrichment_indexing.md §2.4 (index.generation.promoted.v1 event)
- Directives:
  #8: Initial promotion from BUILDING to LIVE writes alias and emits event
  Rollback restores previous generation
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from django.db import connection, connections

from index.generations import (
    GenerationNotFoundError,
    IndexNotReadyError,
    create_generation_partition,
    get_active_generation,
    promote_generation,
    rollback_generation,
)
from index.models import IndexGeneration
from ops.models import EventOutbox

pytestmark = pytest.mark.django_db(databases=["default", "owner"], transaction=True)


@pytest.fixture(autouse=True)
def cleanup_test_partitions() -> Generator[None]:
    """Teardown created test partitions and restore g1 state."""
    yield
    with connections["owner"].cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS plc.chunk_g_test_1 CASCADE;")
        cur.execute("DROP TABLE IF EXISTS plc.chunk_g2 CASCADE;")
        cur.execute("DELETE FROM ops.index_alias WHERE index_family = 'plc_chunks';")
        cur.execute("DELETE FROM ops.index_generation WHERE generation IN ('g_test_1', 'g2');")
        cur.execute(
            """
            UPDATE ops.index_generation
            SET state = 'BUILDING', promoted_at = NULL, rollback_deadline = NULL
            WHERE generation = 'g1';
            """
        )


def test_create_generation_partition() -> None:
    """Verify partition table creation with HNSW, GIN, and B-tree indexes."""
    gen = create_generation_partition(
        index_family="plc_chunks",
        generation="g_test_1",
    )
    assert gen.generation == "g_test_1"
    assert gen.state == "BUILDING"

    # Verify table and indexes in postgres
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'chunk_g_test_1' AND schemaname = 'plc';
            """
        )
        index_names = [r[0] for r in cur.fetchall()]

    assert "chunk_g_test_1_embedding_hnsw" in index_names
    assert "chunk_g_test_1_tsv_gin" in index_names
    assert "chunk_g_test_1_binding_tags_gin" in index_names
    assert "chunk_g_test_1_work_id_idx" in index_names


def test_atomic_promotion_and_rollback() -> None:
    """Verify atomic promotion swap and subsequent rollback restoring previous generation."""
    # Ensure g1 and g2 partitions exist
    create_generation_partition("plc_chunks", "g1")
    create_generation_partition("plc_chunks", "g2")

    # 1. Initial promotion of g1 to LIVE
    alias = promote_generation(
        index_family="plc_chunks",
        to_generation="g1",
        reason="INITIAL_PROMOTION",
    )
    assert alias.generation == "g1"
    assert alias.previous_generation is None
    assert get_active_generation("plc_chunks") == "g1"

    g1_rec = IndexGeneration.objects.get(index_family="plc_chunks", generation="g1")
    assert g1_rec.state == "LIVE"

    # Verify event emitted in outbox
    ev1 = EventOutbox.objects.filter(type="index.generation.promoted.v1").latest("time")
    assert ev1.data["to_generation"] == "g1"
    assert ev1.data["reason"] == "INITIAL_PROMOTION"

    # 2. Promote g2 to LIVE (g1 becomes RETIRED)
    alias2 = promote_generation(
        index_family="plc_chunks",
        to_generation="g2",
        reason="PROMOTION_G2",
    )
    assert alias2.generation == "g2"
    assert alias2.previous_generation == "g1"
    assert get_active_generation("plc_chunks") == "g2"

    g1_rec.refresh_from_db()
    assert g1_rec.state == "RETIRED"
    g2_rec = IndexGeneration.objects.get(index_family="plc_chunks", generation="g2")
    assert g2_rec.state == "LIVE"

    # 3. Rollback from g2 to g1
    alias_rolled = rollback_generation(index_family="plc_chunks")
    assert alias_rolled.generation == "g1"
    assert alias_rolled.previous_generation == "g2"
    assert get_active_generation("plc_chunks") == "g1"

    g1_rec.refresh_from_db()
    assert g1_rec.state == "LIVE"
    g2_rec.refresh_from_db()
    assert g2_rec.state == "ROLLED_BACK"

    # Verify rollback event emitted
    ev_rollback = EventOutbox.objects.filter(type="index.generation.promoted.v1").latest("time")
    assert ev_rollback.data["to_generation"] == "g1"
    assert ev_rollback.data["rolled_back_from"] == "g2"
    assert ev_rollback.data["reason"] == "ROLLBACK"


def test_index_not_ready_error_when_no_alias() -> None:
    """Verify IndexNotReadyError is raised when no active alias exists for family."""
    with pytest.raises(IndexNotReadyError):
        get_active_generation("nonexistent_family")


def test_promote_nonexistent_generation_raises() -> None:
    """Verify GenerationNotFoundError is raised when target generation does not exist."""
    with pytest.raises(GenerationNotFoundError):
        promote_generation("plc_chunks", "nonexistent_g999")
