"""Tests for citation extraction by parsing real fixture PDFs from the IBBI corpus.

Normative source:
- Session S05b Approval Point 8 & User Directive #4:
  "Make test_real_corpus_citations reproducible: commit the 8 source PDFs it cites
   to eval/fixtures/ibbi/ (they are public IBBI orders like the existing fixtures;
   check the legal profile allows it, else use only the 6 already committed).
   Each case must parse the PDF through the pipeline, find the anchor, assert the
   snippet is in that anchor's text, and then check the extractor's output against
   the hand-written expectation. Drop source_pdf as a pure label."
"""

from __future__ import annotations

from pathlib import Path

import pytest

from anchor_lib.ids import mint_id
from parse.citations.extractor import extract_citations_from_anchor
from parse.pipeline import ParsingPipeline


def _find_fixture_dir() -> Path:
    candidates = [
        Path("../eval/fixtures/ibbi"),
        Path("eval/fixtures/ibbi"),
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    raise FileNotFoundError("Could not locate eval/fixtures/ibbi directory")


_PIPELINE = ParsingPipeline()
_PARSED_CACHE: dict[str, dict[str, str]] = {}


def _get_parsed_nodes(pdf_filename: str) -> dict[str, str]:
    """Parse fixture PDF through the pipeline and cache node fragments -> text."""
    if pdf_filename not in _PARSED_CACHE:
        fixture_dir = _find_fixture_dir()
        pdf_path = fixture_dir / pdf_filename
        assert pdf_path.exists(), f"Fixture PDF not found: {pdf_path}"
        data = pdf_path.read_bytes()
        res = _PIPELINE.process(
            data,
            raw_id=f"raw_{pdf_filename}",
            existing_work_id=mint_id("wrk"),
        )
        _PARSED_CACHE[pdf_filename] = {n.anchor_id.split("#")[-1]: n.text for n in res.nodes}
    return _PARSED_CACHE[pdf_filename]


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "test_name",
        "pdf_filename",
        "anchor_fragment",
        "expected_snippet",
        "expected_raw",
        "expected_scheme",
        "expected_normalized",
        "expected_court_hint",
        "expected_pin_kind",
    ),
    [
        # 1. SCC — Saranga Aggarwal
        (
            "scc_mention_saranga_aggarwal",
            "3dd78accf7aff459a4dbf5eb5e2a975e.pdf",
            "p8",
            "(2024) 5 SCC 745",
            "(2024) 5 SCC 745",
            "SCC",
            "(2024) 5 SCC 745",
            None,
            "NONE",
        ),
        # 2. SCC — Ghanshyam Mishra
        (
            "scc_mention_ghanshyam_mishra",
            "11487cc8fdf860689d07fd02e7677b95.pdf",
            "p24",
            "(2021) 9 SCC 657",
            "(2021) 9 SCC 657",
            "SCC",
            "(2021) 9 SCC 657",
            None,
            "NONE",
        ),
        # 3. SCC — Essar Steel CoC
        (
            "scc_mention_essar_steel",
            "11487cc8fdf860689d07fd02e7677b95.pdf",
            "p16",
            "(2020) 8 SCC 531",
            "(2020) 8 SCC 531",
            "SCC",
            "(2020) 8 SCC 531",
            None,
            "NONE",
        ),
        # 4. SCC OnLine — NCLAT
        (
            "scc_online_nclat_standard_chartered",
            "11487cc8fdf860689d07fd02e7677b95.pdf",
            "p16",
            "2019 SCC OnLine NCLAT 388",
            "2019 SCC OnLine NCLAT 388",
            "SCC_ONLINE",
            "2019 SCC OnLine NCLAT 388",
            "crt_IN_NCLAT",
            "NONE",
        ),
        # 5. SCC OnLine — Supreme Court
        (
            "scc_online_sc_rainbow_papers",
            "11487cc8fdf860689d07fd02e7677b95.pdf",
            "p19",
            "2025 SCC OnLine SC 2275",
            "2025 SCC OnLine SC 2275",
            "SCC_ONLINE",
            "2025 SCC OnLine SC 2275",
            "crt_IN_SC",
            "NONE",
        ),
        # 6. SCC OnLine — NCLAT 2024
        (
            "scc_online_nclat_2024",
            "a59818e626e81171b4a517630cf10746.pdf",
            "p19",
            "2024 SCC OnLine NCLAT 1036",
            "2024 SCC OnLine NCLAT 1036",
            "SCC_ONLINE",
            "2024 SCC OnLine NCLAT 1036",
            "crt_IN_NCLAT",
            "NONE",
        ),
        # 7. INSC Neutral Citation — Supreme Court 2026
        (
            "insc_neutral_2026_1046",
            "e9422f2529f4b6d4a3c9b5171aa214fe.pdf",
            "hdr",
            "2026 INSC 1046",
            "2026 INSC 1046",
            "NEUTRAL_INSC",
            "2026 INSC 1046",
            "crt_IN_SC",
            "NONE",
        ),
        # 8. INSC Neutral Citation — Supreme Court 2026
        (
            "insc_neutral_2026_746",
            "3dd78accf7aff459a4dbf5eb5e2a975e.pdf",
            "u1",
            "2026 INSC 746",
            "2026 INSC 746",
            "NEUTRAL_INSC",
            "2026 INSC 746",
            "crt_IN_SC",
            "NONE",
        ),
        # 9. AIR — Supreme Court 2025
        (
            "air_sc_2025_aditya_sarda",
            "99fa1449ee9367d53f7a9f1d75f3a423.pdf",
            "p9",
            "AIR 2025 Supreme Court 2431",
            "AIR 2025 Supreme Court 2431",
            "AIR",
            "AIR 2025 SC 2431",
            "crt_IN_SC",
            "NONE",
        ),
        # 10. AIR — Bombay High Court 2007
        (
            "air_bombay_hc_2007",
            "15019be51394ea0615ab54880b786ee0.pdf",
            "p24",
            "AIR 2007 Bombay 50",
            "AIR 2007 Bombay 50",
            "AIR",
            "AIR 2007 Bom 50",
            "crt_IN_HC_BOM",
            "NONE",
        ),
        # 11. Case Number — NCLT CP (IB)
        (
            "case_no_nclt_cp_ib",
            "nclat_born_digital_del.pdf",
            "p8",
            "CP (IB) No. 567/ND/2025",
            "CP (IB) No. 567/ND/2025",
            "CASE_NO",
            "crt_IN_NCLT_DEL|CP (IB)|567|2025",
            "crt_IN_NCLT_DEL",
            "NONE",
        ),
        # 12. Case Number — NCLAT Company Appeal
        (
            "case_no_nclat_company_appeal",
            "nclat_born_digital_del.pdf",
            "hdr",
            "Company Appeal (AT) (Ins) No. 124 of 2026",
            "Company Appeal (AT) (Ins) No. 124 of 2026",
            "CASE_NO",
            "crt_IN_NCLAT|Company Appeal (AT) (Insolvency)|124|2026",
            "crt_IN_NCLAT",
            "NONE",
        ),
    ],
)
def test_real_corpus_citation_mentions(
    test_name: str,
    pdf_filename: str,
    anchor_fragment: str,
    expected_snippet: str,
    expected_raw: str,
    expected_scheme: str,
    expected_normalized: str,
    expected_court_hint: str | None,
    expected_pin_kind: str,
) -> None:
    """Parse fixture PDF through pipeline, locate anchor, assert snippet in anchor text,

    and verify citation extractor output matches hand-written expectation.
    """
    nodes = _get_parsed_nodes(pdf_filename)
    assert anchor_fragment in nodes, (
        f"[{test_name}] Anchor #{anchor_fragment} not found in {pdf_filename}"
    )

    anchor_text = nodes[anchor_fragment]
    assert expected_snippet in anchor_text, (
        f"[{test_name}] Expected snippet {expected_snippet!r} must be in anchor #{anchor_fragment} of {pdf_filename}. "
        f"Got text: {anchor_text[:120]}..."
    )

    full_anchor_id = f"wrk_test/en#{anchor_fragment}"
    citations = extract_citations_from_anchor(text=anchor_text, anchor_id=full_anchor_id)

    matching = [c for c in citations if c.raw_text == expected_raw]
    assert len(matching) == 1, (
        f"[{test_name}] Expected raw citation {expected_raw!r} in {pdf_filename} #{anchor_fragment}, "
        f"found {[c.raw_text for c in citations]}"
    )

    cite = matching[0]
    assert cite.scheme == expected_scheme
    assert cite.normalized == expected_normalized
    assert cite.court_hint == expected_court_hint
    assert cite.pin.get("kind") == expected_pin_kind
    assert cite.quote_selector["exact"] == expected_raw
    assert cite.anchor_id == full_anchor_id


def test_real_negative_cases_do_not_match() -> None:
    """Verify that text that looks like a citation but is not a case citation does NOT match.

    Examples:
    - Act No. 31 of 2016 (Statute Act number)
    - Order dated 12.05.2021 passed by the Adjudicating Authority (Date reference)
    - Regulation 33 of IBBI (Insolvency Resolution Process for Corporate Persons) Regulations, 2016
    - Notification No. IBBI/2026-27/GN/REG012 dated 31.03.2026 (Gazette notification)
    """
    negative_snippets = [
        "In terms of the Insolvency and Bankruptcy Code, 2016 (Act No. 31 of 2016), the moratorium applies.",
        "The applicant refers to the Order dated 12.05.2021 passed by the Adjudicating Authority in this matter.",
        "In compliance with Regulation 33 of IBBI (Insolvency Resolution Process for Corporate Persons) Regulations, 2016.",
        "Published vide Notification No. IBBI/2026-27/GN/REG012 dated 31.03.2026 in the Gazette of India.",
    ]

    for snippet in negative_snippets:
        citations = extract_citations_from_anchor(
            text=snippet,
            anchor_id="wrk_test/en#p1",
        )
        assert len(citations) == 0, (
            f"Expected 0 case citations in non-citation text {snippet!r}, got: {citations}"
        )
