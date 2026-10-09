"""Tests for plc.index_expression_state and quality invariant quarantine handling.

Normative sources:
- docs/04_P2_enrichment_indexing.md §2.7 (expression state tracking)
- Session S06 Directives:
  #5: Monotonic parse_id check (drops stale parse events based on ULID comparison).
  #5: Monotonic doc_seq increments on re-parse.
  #6: Quarantining a re-parse preserves previous live chunks; stamps last_quarantined_parse_id.
  #6: Fresh parse failing invariants sets status = 'QUARANTINED' and creates 0 chunks.
"""

from __future__ import annotations

import pytest
from django.db import connection

from anchor_lib.ids import mint_id
from index.indexer import IndexPipeline
from index.models import IndexExpressionState

pytestmark = pytest.mark.django_db(databases=["default", "owner"], transaction=True)


def test_stale_parse_dropped_by_ulid_monotonicity() -> None:
    """Assert parse events with parse_id <= accepted_parse_id are dropped as stale."""
    pipeline = IndexPipeline()
    work_id = mint_id("wrk")
    serial_key = f"{work_id}/en"

    older_parse_id = "par_01H00000000000000000000010"
    newer_parse_id = "par_01H00000000000000000000020"

    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO plc.work (work_id, work_type, status, integrity_flags)
            VALUES (%s, 'JUDGMENT', 'ACTIVE', '{}');
            """,
            [work_id],
        )
        cur.execute(
            """
            INSERT INTO plc.index_expression_state (
              serial_key, accepted_parse_id, doc_seq, content_digest, enrichment_level, status, pipeline_version
            ) VALUES (%s, %s, 1, 'sha256:111', 'NONE', 'ACTIVE', 'p2.index@0.1.0|g1');
            """,
            [serial_key, newer_parse_id],
        )
        # Create the older parse run in plc.parse_run
        cur.execute(
            """
            INSERT INTO plc.parse_run (
              parse_id, raw_ids, work_id, expression_key, doc_type,
              parsed_doc_uri, parsed_doc_sha256, quality, gate,
              anchor_changes, rights_class, provenance_tier, pipeline_version, created_at
            ) VALUES (
              %s, '{"raw_1"}', %s, 'en', 'JUDGMENT',
              's3://plc-parsed/mock.json', 'sha256:mock', '{}'::jsonb, 'PASS',
              '{}'::jsonb, 'OFFICIAL', 'OFFICIAL_AGGREGATOR', 'p1.parser@0.1.0|det_v1', now()
            );
            """,
            [older_parse_id, work_id],
        )

    # Attempt to index the older parse
    res = pipeline.index_expression(work_id, parse_id=older_parse_id, force=False)
    assert res.skipped is True
    assert "Stale parse_id" in (res.skip_reason or "")


def test_fresh_quarantine_creates_quarantined_state_and_zero_chunks() -> None:
    """Assert fresh parse failing invariants sets status = 'QUARANTINED' with no chunks."""
    pipeline = IndexPipeline()
    work_id = mint_id("wrk")
    serial_key = f"{work_id}/en"
    parse_id = mint_id("par")

    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO plc.work (work_id, work_type, status, integrity_flags)
            VALUES (%s, 'JUDGMENT', 'ACTIVE', '{}');
            """,
            [work_id],
        )
        cur.execute(
            """
            INSERT INTO plc.parse_run (
              parse_id, raw_ids, work_id, expression_key, doc_type,
              parsed_doc_uri, parsed_doc_sha256, quality, gate,
              anchor_changes, rights_class, provenance_tier, pipeline_version, created_at
            ) VALUES (
              %s, '{"raw_1"}', %s, 'en', 'JUDGMENT',
              's3://plc-parsed/mock.json', 'sha256:mock', '{}'::jsonb, 'QUARANTINED',
              '{}'::jsonb, 'OFFICIAL', 'OFFICIAL_AGGREGATOR', 'p1.parser@0.1.0|det_v1', now()
            );
            """,
            [parse_id, work_id],
        )

    res = pipeline.index_expression(work_id, parse_id=parse_id)
    assert res.quarantined is True
    assert res.chunk_count == 0

    state = IndexExpressionState.objects.get(serial_key=serial_key)
    assert state.status == "QUARANTINED"
    assert state.accepted_parse_id is None
    assert state.doc_seq == 0
    assert state.last_quarantined_parse_id == parse_id

    # Verify zero chunks in database
    with connection.cursor() as cur:
        cur.execute("SELECT count(*) FROM plc.chunk WHERE work_id = %s;", [work_id])
        assert cur.fetchone()[0] == 0


def test_quarantining_reparse_preserves_live_chunks() -> None:
    """Assert subsequent bad re-parse preserves live chunks and updates quarantine audit columns."""
    pipeline = IndexPipeline()
    work_id = mint_id("wrk")
    serial_key = f"{work_id}/en"
    good_parse_id = "par_01H00000000000000000000010"
    bad_reparse_id = "par_01H00000000000000000000020"
    chk_id = mint_id("chk")

    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO plc.work (work_id, work_type, status, integrity_flags)
            VALUES (%s, 'JUDGMENT', 'ACTIVE', '{}');
            """,
            [work_id],
        )
        cur.execute(
            """
            INSERT INTO plc.index_expression_state (
              serial_key, accepted_parse_id, doc_seq, content_digest, enrichment_level, status, pipeline_version
            ) VALUES (%s, %s, 1, 'sha256:good', 'BASE', 'ACTIVE', 'p2.index@0.1.0|g1');
            """,
            [serial_key, good_parse_id],
        )
        # Seed an existing live chunk for this expression
        cur.execute(
            """
            INSERT INTO plc.chunk_g1 (
              chunk_id, index_generation, work_id, expression_key, anchor_ids,
              anchor_first, anchor_last, chunk_kind, context_header, text, text_hash,
              doc_type, rights_class, quality, body, tsv, embedding, doc_seq, pipeline_version
            ) VALUES (
              %s, 'g1', %s, 'en', '{"p1"}',
              'p1', 'p1', 'JUDG_HEADER', 'Header', 'Live Text', 'hash1',
              'JUDGMENT', 'OFFICIAL', '{}'::jsonb, '{}'::jsonb,
              to_tsvector('simple', 'Live Text'),
              ('[' || array_to_string(array_fill(0.0, ARRAY[1024]), ',') || ']')::halfvec,
              1, 'p2.index@0.1.0|g1'
            );
            """,
            [chk_id, work_id],
        )
        # Create bad reparse with QUARANTINE gate
        cur.execute(
            """
            INSERT INTO plc.parse_run (
              parse_id, raw_ids, work_id, expression_key, doc_type,
              parsed_doc_uri, parsed_doc_sha256, quality, gate,
              anchor_changes, rights_class, provenance_tier, pipeline_version, created_at
            ) VALUES (
              %s, '{"raw_1"}', %s, 'en', 'JUDGMENT',
              's3://plc-parsed/bad.json', 'sha256:bad', '{}'::jsonb, 'QUARANTINED',
              '{}'::jsonb, 'OFFICIAL', 'OFFICIAL_AGGREGATOR', 'p1.parser@0.1.0|det_v1', now()
            );
            """,
            [bad_reparse_id, work_id],
        )

    # Execute reparse indexing
    res = pipeline.index_expression(work_id, parse_id=bad_reparse_id)
    assert res.quarantined is True

    # Assert previous live chunks are preserved!
    with connection.cursor() as cur:
        cur.execute("SELECT count(*) FROM plc.chunk WHERE work_id = %s;", [work_id])
        assert cur.fetchone()[0] == 1

    # Assert state remains ACTIVE, accepted_parse_id untouched, quarantine audit populated
    state = IndexExpressionState.objects.get(serial_key=serial_key)
    assert state.status == "ACTIVE"
    assert state.accepted_parse_id == good_parse_id
    assert state.doc_seq == 1
    assert state.last_quarantined_parse_id == bad_reparse_id
    assert state.quarantine_reasons is not None
