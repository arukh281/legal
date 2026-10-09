"""Tests for canonical work filtering and merge/split lifecycle in index pipeline.

Normative sources:
- Session S06 Plan §7.5 (test_canonical_filter)
- Directives:
  #4: On identity.merged.v1, from_id state is REKEYED, chunks deleted, doc.indexed.v1 emitted.
  #5: Forced re-index path for identity events and index_corpus.
  STUB and MERGED works are strictly skipped.
"""

from __future__ import annotations

import datetime
import pytest
from django.db import connection

from anchor_lib.ids import mint_id
from index.consumer import handle_identity_merged, handle_identity_split
from index.indexer import IndexPipeline
from index.models import Chunk, IndexExpressionState
from ops.models import EventOutbox

pytestmark = pytest.mark.django_db(databases=["default", "owner"], transaction=True)


def test_stub_and_merged_works_are_skipped() -> None:
    """Assert STUB and MERGED works are never indexed."""
    pipeline = IndexPipeline()

    stub_id = mint_id("wrk")
    merged_id = mint_id("wrk")

    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO plc.work (work_id, work_type, status, integrity_flags)
            VALUES
              (%s, 'JUDGMENT', 'STUB', '{}'),
              (%s, 'JUDGMENT', 'MERGED', '{}');
            """,
            [stub_id, merged_id],
        )

    res_stub = pipeline.index_expression(stub_id)
    assert res_stub.skipped is True
    assert "STUB" in (res_stub.skip_reason or "")
    assert res_stub.chunk_count == 0

    res_merged = pipeline.index_expression(merged_id)
    assert res_merged.skipped is True
    assert "MERGED" in (res_merged.skip_reason or "")
    assert res_merged.chunk_count == 0


def test_identity_merged_lifecycle() -> None:
    """Assert identity.merged.v1 deletes from_id chunks, sets status REKEYED, and emits removal event."""
    pipeline = IndexPipeline()

    from_id = mint_id("wrk")
    to_id = mint_id("wrk")

    # Set up from_id state and mock chunk
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO plc.work (work_id, work_type, status, integrity_flags)
            VALUES
              (%s, 'JUDGMENT', 'MERGED', '{}'),
              (%s, 'JUDGMENT', 'ACTIVE', '{}');
            """,
            [from_id, to_id],
        )
        cur.execute(
            """
            INSERT INTO plc.index_expression_state (
              serial_key, accepted_parse_id, doc_seq, content_digest, enrichment_level, status, pipeline_version
            ) VALUES (%s, %s, 1, 'sha256:111', 'NONE', 'ACTIVE', 'p2.index@0.1.0|g1');
            """,
            [f"{from_id}/en", mint_id("prs")],
        )

    # Insert a dummy chunk in plc.chunk_g1
    chk_id = mint_id("chk")
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO plc.chunk_g1 (
              chunk_id, index_generation, work_id, expression_key, anchor_ids,
              anchor_first, anchor_last, chunk_kind, context_header, text, text_hash,
              doc_type, rights_class, quality, body, tsv, embedding, doc_seq, pipeline_version
            ) VALUES (
              %s, 'g1', %s, 'en', '{"p1"}',
              'p1', 'p1', 'JUDG_HEADER', 'Header', 'Text', 'hash1',
              'JUDGMENT', 'OFFICIAL', '{}'::jsonb, '{}'::jsonb,
              to_tsvector('simple', 'Text'),
              ('[' || array_to_string(array_fill(0.0, ARRAY[1024]), ',') || ']')::halfvec,
              1, 'p2.index@0.1.0|g1'
            );
            """,
            [chk_id, from_id],
        )

    # Execute merge handling
    event = {
        "type": "identity.merged.v1",
        "data": {
            "from_id": from_id,
            "to_id": to_id,
            "reason": "OFFICIAL_DEDUPE",
        },
    }
    res = handle_identity_merged(event)
    assert res["status"] == "SUCCESS"
    assert res["removed_chunk_count"] == 1

    # Verify chunks deleted for from_id
    with connection.cursor() as cur:
        cur.execute("SELECT count(*) FROM plc.chunk WHERE work_id = %s;", [from_id])
        assert cur.fetchone()[0] == 0

        # Verify state is REKEYED
        cur.execute(
            "SELECT status FROM plc.index_expression_state WHERE serial_key = %s;",
            [f"{from_id}/en"],
        )
        assert cur.fetchone()[0] == "REKEYED"

    # Verify doc.indexed.v1 removal event emitted
    ev = EventOutbox.objects.filter(type="doc.indexed.v1", subject=f"{from_id}/en").latest("time")
    assert ev.data["removed_chunk_ids"] == [chk_id]
    assert ev.data["parse_id"] == "REKEYED"


def test_identity_split_lifecycle() -> None:
    """Assert identity.split.v1 triggers forced re-indexing for split works."""
    w1 = mint_id("wrk")
    w2 = mint_id("wrk")

    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO plc.work (work_id, work_type, status, integrity_flags)
            VALUES
              (%s, 'JUDGMENT', 'ACTIVE', '{}'),
              (%s, 'JUDGMENT', 'ACTIVE', '{}');
            """,
            [w1, w2],
        )

    event = {
        "type": "identity.split.v1",
        "data": {
            "split_works": [w1, w2],
        },
    }
    res = handle_identity_split(event)
    assert res["status"] == "SUCCESS"
    assert len(res["results"]) == 2
    assert res["results"][0]["work_id"] == w1
    assert res["results"][1]["work_id"] == w2
