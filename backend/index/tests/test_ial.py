"""Tests for Index Access Layer (IAL).

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.5
- docs/04_P2_enrichment_indexing.md §2.5, §5.11a
- Directives:
  #1: Quoted tsquery terms for lexemes combined with websearch_to_tsquery for remaining text
  #7: GenerationGone typed exception carrying anchor_ids on retired generation
  Single-leg retrieval only (LEXICAL or DENSE), raw scores, hybrid mode rejected
"""

from __future__ import annotations

import datetime
import json
from collections.abc import Generator

import pytest
from django.db import connection, connections

from index.ial import (
    GenerationGone,
    IndexAccessLayer,
    IndexQuery,
    UnsupportedFilterError,
)
from index.models import IndexGeneration
from index.normalizer import extract_legal_lexemes

pytestmark = pytest.mark.django_db(databases=["default", "owner"], transaction=True)


@pytest.fixture(autouse=True)
def ensure_g1_and_cleanup() -> Generator[None]:
    """Ensure g1 partition and active alias exist, clean up test chunks afterwards."""
    # Ensure active alias points to g1
    with connections["owner"].cursor() as cur:
        cur.execute(
            """
            UPDATE ops.index_generation
            SET state = 'LIVE', promoted_at = now()
            WHERE index_family = 'plc_chunks' AND generation = 'g1';
            """
        )
        cur.execute(
            """
            INSERT INTO ops.index_alias (index_family, generation, swapped_at)
            VALUES ('plc_chunks', 'g1', now())
            ON CONFLICT (index_family) DO UPDATE SET generation = 'g1';
            """
        )

    yield

    with connections["owner"].cursor() as cur:
        cur.execute("DELETE FROM plc.chunk_g1 WHERE chunk_id LIKE 'chk_test_%';")
        cur.execute("DELETE FROM ops.index_generation WHERE generation LIKE 'g_test_%';")
        cur.execute(
            """
            UPDATE ops.index_generation
            SET state = 'LIVE'
            WHERE index_family = 'plc_chunks' AND generation = 'g1';
            """
        )


def _insert_chunk(
    chunk_id: str,
    work_id: str,
    text: str,
    context_header: str = "Order Details",
    anchor_ids: list[str] | None = None,
    court_id: str = "nclt_delhi",
    court_level: str = "TRIBUNAL",
    decision_date: datetime.date | None = datetime.date(2024, 5, 10),
    doc_type: str = "ORDER",
    binding_scope_tags: list[str] | None = None,
    vector: list[float] | None = None,
    doc_seq: int = 1,
    generation: str = "g1",
) -> None:
    """Helper to insert a chunk with populated tsv and embedding into plc.chunk partition."""
    anchors = anchor_ids or [f"{chunk_id}_anc_1"]
    tags = binding_scope_tags or ["bench:nclt_delhi", "circuit:delhi"]
    if vector is None:
        vector = [0.0] * 1024
    vec_str = "[" + ",".join(str(x) for x in vector) + "]"

    lexemes = extract_legal_lexemes(f"{context_header} {text}")

    sql = f"""
    INSERT INTO plc.chunk_{generation} (
        chunk_id, index_generation, work_id, expression_key,
        anchor_ids, anchor_first, anchor_last, chunk_kind,
        rhetorical_role, opinion_role, context_header, text, text_hash,
        court_id, court_level, bench_strength, decision_date, doc_type,
        binding_scope_tags, cited_work_ids, cited_provision_anchors,
        valid_from, valid_to, in_force, trust_label, rights_class,
        quality, body, tsv, embedding, doc_seq, pipeline_version
    ) VALUES (
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s,
        (
            setweight(to_tsvector('public.legal_en', %s), 'A') ||
            setweight(to_tsvector('public.legal_en', %s), 'B') ||
            setweight(array_to_tsvector(%s::text[]), 'C')
        ),
        %s::halfvec(1024), %s, %s
    );
    """
    with connection.cursor() as cur:
        cur.execute(
            sql,
            [
                chunk_id,
                generation,
                work_id,
                "en",
                anchors,
                anchors[0],
                anchors[-1],
                "ORDER_BODY",
                None,
                None,
                context_header,
                text,
                "hash_" + chunk_id,
                court_id,
                court_level,
                2,
                decision_date,
                doc_type,
                tags,
                [],
                [],
                None,
                None,
                True,
                "PLC_OFFICIAL",
                "PUBLIC_DOMAIN",
                json.dumps({}),
                json.dumps({}),
                context_header,
                text,
                lexemes,
                vec_str,
                doc_seq,
                "p2.index@0.1.0|g1",
            ],
        )


def test_search_lexical_basic_and_scoring() -> None:
    """Lexical search returns matching chunks ranked by ts_rank_cd."""
    _insert_chunk(
        chunk_id="chk_test_lex_1",
        work_id="wrk_test_1",
        text="The corporate debtor admitted default under Section 7 of the Insolvency and Bankruptcy Code.",
        context_header="NCLT Principal Bench Admission Order",
    )
    _insert_chunk(
        chunk_id="chk_test_lex_2",
        work_id="wrk_test_2",
        text="Application under Section 9 was dismissed due to pre-existing operational debt dispute.",
        context_header="NCLT Mumbai Bench Dismissal Order",
    )

    ial = IndexAccessLayer()
    results = ial.search(IndexQuery(mode="LEXICAL", text="section 7 corporate debtor default"))

    assert len(results) >= 1
    assert results[0].chunk_id == "chk_test_lex_1"
    assert results[0].work_id == "wrk_test_1"
    assert results[0].score > 0.0
    assert "Section 7" in results[0].text


def test_search_lexical_more_relevant_ranks_first_and_tiebreak() -> None:
    """Item 2: Chunks with search terms in context header/body rank above incidental mentions, with tiebreak."""
    # Chunk A: highly relevant to 'Section 7' (in header weight A and body weight B multiple times)
    _insert_chunk(
        chunk_id="chk_test_sec7_primary",
        work_id="wrk_test_sec7_pri",
        context_header="Supreme Court of India | Section 7 IBC Admission",
        text="Application under Section 7 of the IBC filed by financial creditor. Section 7 default proved.",
        anchor_ids=["wrk_test_sec7_pri/en#p1"],
    )
    # Chunk B: passing / incidental mention of 'section 7' (header has no mention, body has single mention)
    _insert_chunk(
        chunk_id="chk_test_sec7_incidental",
        work_id="wrk_test_sec7_inc",
        context_header="NCLT Procedural Adjournment Order",
        text="Matter adjourned. Brief reference to notice under section 7 was noted.",
        anchor_ids=["wrk_test_sec7_inc/en#p1"],
    )

    ial = IndexAccessLayer()
    hits = ial.search(IndexQuery(mode="LEXICAL", text="Section 7", k=10))

    sec7_hits = [h for h in hits if h.chunk_id in ("chk_test_sec7_primary", "chk_test_sec7_incidental")]
    assert len(sec7_hits) == 2
    # The more relevant chunk must rank FIRST with strictly higher score
    assert sec7_hits[0].chunk_id == "chk_test_sec7_primary"
    assert sec7_hits[1].chunk_id == "chk_test_sec7_incidental"
    assert sec7_hits[0].score > sec7_hits[1].score

    # Deterministic tiebreak: when score is identical, order by work_id ASC, anchor_first ASC
    _insert_chunk(
        chunk_id="chk_test_tie_z",
        work_id="wrk_test_tie_z",
        context_header="Identical Order Header",
        text="Identical text body discussing specific section 999 terms.",
        anchor_ids=["wrk_test_tie_z/en#p1"],
    )
    _insert_chunk(
        chunk_id="chk_test_tie_a",
        work_id="wrk_test_tie_a",
        context_header="Identical Order Header",
        text="Identical text body discussing specific section 999 terms.",
        anchor_ids=["wrk_test_tie_a/en#p1"],
    )

    tie_hits = ial.search(IndexQuery(mode="LEXICAL", text="section 999", k=10))
    tie_results = [h for h in tie_hits if h.chunk_id in ("chk_test_tie_a", "chk_test_tie_z")]
    assert len(tie_results) == 2
    # Equal scores break tie deterministically on work_id ASC
    assert pytest.approx(tie_results[0].score, rel=1e-5) == tie_results[1].score
    assert tie_results[0].chunk_id == "chk_test_tie_a"
    assert tie_results[1].chunk_id == "chk_test_tie_z"


def test_search_lexical_filters() -> None:
    """Lexical search filters apply strictly to court_ids, doc_types, dates, and tags."""
    _insert_chunk(
        chunk_id="chk_test_flt_1",
        work_id="wrk_test_flt_1",
        text="Liquidation ordered under section 33 for the corporate debtor.",
        court_id="nclt_delhi",
        decision_date=datetime.date(2023, 1, 15),
        binding_scope_tags=["bench:nclt_delhi"],
    )
    _insert_chunk(
        chunk_id="chk_test_flt_2",
        work_id="wrk_test_flt_2",
        text="Liquidation ordered under section 33 for another corporate debtor.",
        court_id="nclt_mumbai",
        decision_date=datetime.date(2024, 6, 20),
        binding_scope_tags=["bench:nclt_mumbai"],
    )

    ial = IndexAccessLayer()

    # Filter by court_ids
    hits = ial.search(
        IndexQuery(
            mode="LEXICAL",
            text="liquidation section 33",
            filters={"court_ids": ["nclt_delhi"]},
        )
    )
    assert len(hits) == 1
    assert hits[0].chunk_id == "chk_test_flt_1"

    # Filter by date
    hits_date = ial.search(
        IndexQuery(
            mode="LEXICAL",
            text="liquidation section 33",
            filters={"decided_on_or_after": datetime.date(2024, 1, 1)},
        )
    )
    assert len(hits_date) == 1
    assert hits_date[0].chunk_id == "chk_test_flt_2"

    # Filter by tags
    hits_tags = ial.search(
        IndexQuery(
            mode="LEXICAL",
            text="liquidation section 33",
            filters={"binding_scope_tags_any": ["bench:nclt_mumbai"]},
        )
    )
    assert len(hits_tags) == 1
    assert hits_tags[0].chunk_id == "chk_test_flt_2"


def test_search_dense_basic_and_scoring() -> None:
    """Dense search returns chunks ordered by halfvec cosine distance."""
    # Create two orthogonal-ish unit vectors
    v1 = [0.0] * 1024
    v1[0] = 1.0  # matches query perfectly

    v2 = [0.0] * 1024
    v2[1] = 1.0  # orthogonal to query

    _insert_chunk(
        chunk_id="chk_test_dense_1",
        work_id="wrk_dense_1",
        text="Highly relevant text vector 1",
        vector=v1,
    )
    _insert_chunk(
        chunk_id="chk_test_dense_2",
        work_id="wrk_dense_2",
        text="Less relevant text vector 2",
        vector=v2,
    )

    query_vec = [0.0] * 1024
    query_vec[0] = 1.0

    ial = IndexAccessLayer()
    hits = ial.search(IndexQuery(mode="DENSE", vector=query_vec, k=10))

    assert len(hits) >= 2
    assert hits[0].chunk_id == "chk_test_dense_1"
    # Cosine similarity for identical unit vector is ~1.0
    assert pytest.approx(hits[0].score, abs=1e-3) == 1.0
    assert hits[1].chunk_id == "chk_test_dense_2"
    assert hits[1].score < hits[0].score


def test_search_dense_explain_hnsw() -> None:
    """EXPLAIN query with enable_seqscan = off proves HNSW index scan is used."""
    query_vec = [0.0] * 1024
    vec_str = "[" + ",".join(str(x) for x in query_vec) + "]"

    with connection.cursor() as cur:
        cur.execute("SET LOCAL enable_seqscan = off;")
        cur.execute(
            """
            EXPLAIN SELECT chunk_id
            FROM plc.chunk_g1
            ORDER BY (embedding::halfvec(1024)) <=> %s::halfvec(1024)
            LIMIT 5;
            """,
            [vec_str],
        )
        plan_rows = [r[0] for r in cur.fetchall()]

    plan_text = "\n".join(plan_rows)
    assert "Index Scan using chunk_g1_embedding_hnsw on chunk_g1" in plan_text


def test_sql_round_trip_legal_lexemes() -> None:
    """SQL round-trip verifying legal lexemes (138(1)(a) -> s138_1_a and ancestors) via to_tsvector and tsquery."""
    # 1. Direct SQL evaluation of tsvector @@ tsquery
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT (
                setweight(to_tsvector('public.legal_en', 'Dishonour of cheque under Section 138(1)(a) of NI Act'), 'B') ||
                setweight(array_to_tsvector(ARRAY['s138', 's138_1', 's138_1_a']), 'C')
            ) @@ '''s138'''::tsquery AS match_ancestor,
            (
                setweight(to_tsvector('public.legal_en', 'Dishonour of cheque under Section 138(1)(a) of NI Act'), 'B') ||
                setweight(array_to_tsvector(ARRAY['s138', 's138_1', 's138_1_a']), 'C')
            ) @@ '''s138_1_a'''::tsquery AS match_exact;
            """
        )
        row = cur.fetchone()
        assert row is not None
        assert row[0] is True  # Ancestor s138 matches!
        assert row[1] is True  # Exact s138_1_a matches!

    # 2. Insert chunk with 138(1)(a) and CP(IB) case number
    _insert_chunk(
        chunk_id="chk_test_lex_rt_1",
        work_id="wrk_test_rt_1",
        text="Application in CP(IB) 188 of 2026 alleging breach of Section 138(1)(a).",
        context_header="Proceedings under Negotiable Instruments Act",
    )

    ial = IndexAccessLayer()

    # Query for ancestor "section 138"
    hits_sec = ial.search(IndexQuery(mode="LEXICAL", text="section 138"))
    assert len(hits_sec) >= 1
    assert any(h.chunk_id == "chk_test_lex_rt_1" for h in hits_sec)

    # Query for exact section "138(1)(a)"
    hits_exact = ial.search(IndexQuery(mode="LEXICAL", text="138(1)(a)"))
    assert len(hits_exact) >= 1
    assert any(h.chunk_id == "chk_test_lex_rt_1" for h in hits_exact)

    # Query for case number "CP (IB) 188 of 2026"
    hits_case = ial.search(IndexQuery(mode="LEXICAL", text="CP (IB) 188 of 2026"))
    assert len(hits_case) >= 1
    assert any(h.chunk_id == "chk_test_lex_rt_1" for h in hits_case)


def test_mode_and_filter_validation() -> None:
    """Unsupported modes (e.g. HYBRID) and unknown filters raise explicit errors."""
    ial = IndexAccessLayer()

    # HYBRID mode must be rejected per Directive
    with pytest.raises(ValueError, match="Invalid search mode 'HYBRID'"):
        ial.search(IndexQuery(mode="HYBRID", text="sample"))

    with pytest.raises(ValueError, match="Must be 'LEXICAL' or 'DENSE'"):
        ial.search(IndexQuery(mode="INVALID_MODE", text="sample"))

    # Unsupported filter raises UnsupportedFilterError
    with pytest.raises(UnsupportedFilterError, match="not supported"):
        ial.search(
            IndexQuery(
                mode="LEXICAL",
                text="sample",
                filters={"unsupported_filter_name": "val"},
            )
        )


def test_get_chunks_and_generation_gone() -> None:
    """get_chunks retrieves chunks by IDs, raising GenerationGone if generation is retired."""
    _insert_chunk(
        chunk_id="chk_test_gc_1",
        work_id="wrk_gc_1",
        text="First chunk for get_chunks test.",
        anchor_ids=["anc_gc_1", "anc_gc_2"],
    )

    ial = IndexAccessLayer()
    hits = ial.get_chunks(["chk_test_gc_1"])
    assert len(hits) == 1
    assert hits[0].chunk_id == "chk_test_gc_1"
    assert hits[0].anchor_ids == ["anc_gc_1", "anc_gc_2"]

    # Mark g1 as RETIRED
    IndexGeneration.objects.filter(index_family="plc_chunks", generation="g1").update(
        state="RETIRED"
    )

    with pytest.raises(GenerationGone) as exc_info:
        ial.get_chunks(["chk_test_gc_1"], generation="g1")

    assert exc_info.value.generation == "g1"
    assert "anc_gc_1" in exc_info.value.anchor_ids


def test_get_neighbours() -> None:
    """get_neighbours returns contiguous chunks surrounding the target anchor."""
    work_id = "wrk_test_neigh"
    _insert_chunk(
        chunk_id="chk_test_n_1",
        work_id=work_id,
        text="Para 1 preamble",
        anchor_ids=["anc_p1"],
        doc_seq=1,
    )
    _insert_chunk(
        chunk_id="chk_test_n_2",
        work_id=work_id,
        text="Para 2 facts",
        anchor_ids=["anc_p2"],
        doc_seq=2,
    )
    _insert_chunk(
        chunk_id="chk_test_n_3",
        work_id=work_id,
        text="Para 3 finding",
        anchor_ids=["anc_p3"],
        doc_seq=3,
    )

    ial = IndexAccessLayer()
    neighbours = ial.get_neighbours(anchor_id="anc_p2", before=1, after=1)

    assert len(neighbours) == 3
    assert [n.chunk_id for n in neighbours] == [
        "chk_test_n_1",
        "chk_test_n_2",
        "chk_test_n_3",
    ]
