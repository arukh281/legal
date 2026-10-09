"""Tests for legal lexeme normaliser and real Postgres SQL round trip.

Normative sources:
- Session S06 Directive #1:
  - Extract section paths (138(1)(a), 7(5)), penal combos (302/34), u/s, r/w,
    Art. 21A, CP(IB) case numbers, SCC/AIR/INSC citations.
  - Map each to canonical lexemes and emit ancestor lexemes.
  - Real SQL round-trip test using setweight(array_to_tsvector($lexemes::text[]), 'C')
    and direct tsquery terms combined with websearch_to_tsquery.
"""

from __future__ import annotations

import pytest
from django.db import connection

from index.normalizer import extract_legal_lexemes, extract_query_lexemes


def test_extract_sections_and_ancestors() -> None:
    """Verify section extraction and ancestor expansion."""
    # 138(1)(a) -> s138, s138_1, s138_1_a
    lexemes = extract_legal_lexemes("The offence under Section 138(1)(a) is made out.")
    assert "s138" in lexemes
    assert "s138_1" in lexemes
    assert "s138_1_a" in lexemes

    # Section 7(5)
    lex = extract_legal_lexemes("Petition admitted under Section 7(5) of the Code.")
    assert "s7" in lex
    assert "s7_5" in lex

    # Simple Section 7
    lex_simple = extract_legal_lexemes("Application filed under section 7 of IBC.")
    assert "s7" in lex_simple


def test_extract_penal_combos_articles_shortcuts() -> None:
    """Verify penal combos, constitutional articles, and procedural shortcuts."""
    # Penal combo 302/34
    lex = extract_legal_lexemes("Charged under 302/34 IPC.")
    assert "s302" in lex
    assert "s34" in lex
    assert "s302_34" in lex

    # Article 21A
    lex_art = extract_legal_lexemes("Invoking Art. 21A of the Constitution.")
    assert "art21" in lex_art
    assert "art21a" in lex_art

    # Article 141
    lex_art141 = extract_legal_lexemes("Binding per Article 141.")
    assert "art141" in lex_art141

    # u/s and r/w
    lex_proc = extract_legal_lexemes("Application u/s 9 r/w Section 5.")
    assert "lex_u_s" in lex_proc
    assert "lex_r_w" in lex_proc
    assert "s9" in lex_proc
    assert "s5" in lex_proc


def test_extract_cpib_case_numbers() -> None:
    """Verify NCLT CP(IB) case numbers in various formats."""
    # Bench with slash
    lex1 = extract_legal_lexemes("In CP(IB) No. 1234/MB/2019 order passed.")
    assert "cp_ib_1234_mb_2019" in lex1
    assert "cp_ib_1234_2019" in lex1

    # CP(IB) 188 of 2026
    lex2 = extract_legal_lexemes("In the matter of Takshashila [CP(IB) 188 of 2026].")
    assert "cp_ib_188_2026" in lex2

    # CP(IB)/66/7/AMR/2024
    lex3 = extract_legal_lexemes("Disposing of CP(IB)/66/7/AMR/2024.")
    assert "cp_ib_66_amr_2024" in lex3
    assert "cp_ib_66_2024" in lex3

    # CP(IB)/247(MB)/2026
    lex4 = extract_legal_lexemes("Petition in CP(IB)/247(MB)/2026.")
    assert "cp_ib_247_mb_2026" in lex4
    assert "cp_ib_247_2026" in lex4


def test_extract_query_lexemes_and_remaining() -> None:
    """Verify separation of extracted lexemes and clean remaining search text."""
    lexemes, remaining = extract_query_lexemes("section 7 of IBC")
    assert "s7" in lexemes
    assert remaining == "of IBC"

    lexemes_cpi, remaining_cpi = extract_query_lexemes("CP(IB) 188 of 2026")
    assert "cp_ib_188_2026" in lexemes_cpi
    assert remaining_cpi == ""

    lexemes_plain, remaining_plain = extract_query_lexemes("insolvency resolution process")
    assert lexemes_plain == []
    assert remaining_plain == "insolvency resolution process"


@pytest.mark.django_db
def test_real_sql_roundtrip_directive_1() -> None:
    """Directive #1: Test real Postgres SQL round trip with array_to_tsvector at weight C.

    Asserts:
    1. Lexemes survive without underscore splitting.
    2. Exact tsquery matches.
    3. Ancestor search ('section 138') finds chunk indexed with '138(1)(a)'.
    4. Combined websearch on remaining prose + quoted lexemes tsquery matches.
    """
    chunk_header = "NCLT New Delhi | 2024-02-05"
    chunk_text = "The applicant filed under Section 138(1)(a) regarding dishonour of cheque."
    lexemes = extract_legal_lexemes(f"{chunk_header} {chunk_text}")
    assert "s138" in lexemes
    assert "s138_1_a" in lexemes

    with connection.cursor() as cur:
        # Build index tsvector
        cur.execute(
            """
            SELECT (
                setweight(to_tsvector('public.legal_en', %s), 'A') ||
                setweight(to_tsvector('public.legal_en', %s), 'B') ||
                setweight(array_to_tsvector(%s::text[]), 'C')
            );
            """,
            [chunk_header, chunk_text, lexemes],
        )
        vec_row = cur.fetchone()
        assert vec_row is not None

        # 1. Exact query for 'section 138(1)(a)'
        q_lex, _ = extract_query_lexemes("section 138(1)(a)")
        assert "s138_1_a" in q_lex
        cur.execute(
            """
            SELECT (
                setweight(to_tsvector('public.legal_en', %s), 'A') ||
                setweight(to_tsvector('public.legal_en', %s), 'B') ||
                setweight(array_to_tsvector(%s::text[]), 'C')
            ) @@ '''s138_1_a'''::tsquery;
            """,
            [chunk_header, chunk_text, lexemes],
        )
        assert cur.fetchone()[0] is True

        # 2. Ancestor query for 'section 138' matches the chunk
        q_anc_lex, _ = extract_query_lexemes("section 138")
        assert "s138" in q_anc_lex
        cur.execute(
            """
            SELECT (
                setweight(to_tsvector('public.legal_en', %s), 'A') ||
                setweight(to_tsvector('public.legal_en', %s), 'B') ||
                setweight(array_to_tsvector(%s::text[]), 'C')
            ) @@ '''s138'''::tsquery;
            """,
            [chunk_header, chunk_text, lexemes],
        )
        assert cur.fetchone()[0] is True

        # 3. Combined query: 'section 138 dishonour'
        cur.execute(
            """
            SELECT (
                setweight(to_tsvector('public.legal_en', %s), 'A') ||
                setweight(to_tsvector('public.legal_en', %s), 'B') ||
                setweight(array_to_tsvector(%s::text[]), 'C')
            ) @@ ('''s138'''::tsquery && websearch_to_tsquery('public.legal_en', 'dishonour'));
            """,
            [chunk_header, chunk_text, lexemes],
        )
        assert cur.fetchone()[0] is True
