"""Tests for citation extraction from text and anchor objects.

Normative sources:
- docs/03_P1_ingestion_parsing.md §5.8
- docs/mvp/03_data_model_and_contracts.md §3.3
- S05b Directives:
  - Reporter schemes (SCC, SCC OnLine, AIR, SCR, INSC, Neutral HC)
  - Case numbers (NCLT CP(IB), NCLAT Company Appeal)
  - Pinpoints (paras, pp.)
  - QuoteSelector (prefix, exact, suffix)
  - Degraded quality flags (ocr_conf < 0.80, hidden text)
"""

from datetime import date

from parse.citations.extractor import (
    extract_citations_from_anchor,
)


def test_extract_scc_citation() -> None:
    text = "The Supreme Court in Swiss Ribbons Pvt. Ltd. v. Union of India, (2019) 4 SCC 17 held that the preamble..."
    cites = extract_citations_from_anchor(
        anchor_id="wrk_test/en#p1",
        text=text,
        decision_date=date(2023, 5, 10),
    )
    assert len(cites) == 1
    c = cites[0]
    assert c.scheme == "SCC"
    assert c.normalized == "(2019) 4 SCC 17"
    assert c.raw_text == "(2019) 4 SCC 17"
    assert c.court_hint is None  # Never infer court from reporter
    assert c.date_hint == "2019"
    assert c.temporal_check == "OK"
    assert c.quote_selector["exact"] == "(2019) 4 SCC 17"
    assert "Union of India" in c.quote_selector["prefix"]
    assert "held that" in c.quote_selector["suffix"]


def test_extract_scc_online_with_court() -> None:
    text = "Reliance is placed on 2023 SCC OnLine NCLAT 839 at para 14 where it was noted..."
    cites = extract_citations_from_anchor(
        anchor_id="wrk_test/en#p2",
        text=text,
        decision_date=date(2024, 1, 1),
    )
    assert len(cites) == 1
    c = cites[0]
    assert c.scheme == "SCC_ONLINE"
    assert c.normalized == "2023 SCC OnLine NCLAT 839"
    assert c.court_hint == "crt_IN_NCLAT"
    assert c.date_hint == "2023"
    assert c.pin["kind"] == "PARA"
    assert c.pin["value"] == "14"


def test_extract_air_and_scr() -> None:
    text = "See AIR 1968 SC 1432 and also [1968] 3 SCR 724 for earlier precedents."
    cites = extract_citations_from_anchor(
        anchor_id="wrk_test/en#p3",
        text=text,
    )
    assert len(cites) == 2
    schemes = {c.scheme for c in cites}
    assert schemes == {"AIR", "SCR"}
    air = next(c for c in cites if c.scheme == "AIR")
    assert air.normalized == "AIR 1968 SC 1432"
    assert air.court_hint == "crt_IN_SC"
    scr = next(c for c in cites if c.scheme == "SCR")
    assert scr.normalized == "[1968] 3 SCR 724"


def test_extract_insc_neutral() -> None:
    text = "Recently in 2024 INSC 45, the Apex Court clarified..."
    cites = extract_citations_from_anchor(
        anchor_id="wrk_test/en#p4",
        text=text,
    )
    assert len(cites) == 1
    c = cites[0]
    assert c.scheme == "NEUTRAL_INSC"
    assert c.normalized == "2024 INSC 45"
    assert c.court_hint == "crt_IN_SC"


def test_extract_delhi_hc_neutral() -> None:
    text = "As observed in 2023:DHC:1234, the scope of Section 9 is limited."
    cites = extract_citations_from_anchor(
        anchor_id="wrk_test/en#p5",
        text=text,
    )
    assert len(cites) == 1
    c = cites[0]
    assert c.scheme == "NEUTRAL_HC"
    assert c.normalized == "2023:DHC:1234"
    assert c.court_hint == "crt_IN_HC_DEL"


def test_extract_nclt_case_number() -> None:
    text = "filed in Company Petition (IB) No. 149 of 2023 before the Adjudicating Authority."
    cites = extract_citations_from_anchor(
        anchor_id="wrk_test/en#p6",
        text=text,
    )
    assert len(cites) == 1
    c = cites[0]
    assert c.scheme == "CASE_NO"
    assert c.court_hint == "crt_IN_NCLT"
    assert c.normalized == "crt_IN_NCLT|CP (IB)|149|2023"


def test_extract_nclat_company_appeal() -> None:
    text = "challenging the order in Company Appeal (AT) (Insolvency) No. 123 of 2021."
    cites = extract_citations_from_anchor(
        anchor_id="wrk_test/en#p7",
        text=text,
    )
    assert len(cites) == 1
    c = cites[0]
    assert c.scheme == "CASE_NO"
    assert c.court_hint == "crt_IN_NCLAT"
    assert c.normalized == "crt_IN_NCLAT|Company Appeal (AT) (Insolvency)|123|2021"


def test_case_number_without_court() -> None:
    text = "arising out of Civil Appeal No. 2594 of 2026."
    cites = extract_citations_from_anchor(
        anchor_id="wrk_test/en#p8",
        text=text,
    )
    assert len(cites) == 1
    c = cites[0]
    assert c.scheme == "CASE_NO"
    assert c.court_hint is None
    # Court not stated: normalized key has empty court prefix
    assert c.normalized == "|Civil Appeal|2594|2026"


def test_future_citation_detection() -> None:
    # Document decided in 2018 cites a (2024) judgment (impossible in real time)
    text = "Refer to (2024) 5 SCC 745."
    cites = extract_citations_from_anchor(
        anchor_id="wrk_test/en#p9",
        text=text,
        decision_date=date(2018, 1, 1),
    )
    assert len(cites) == 1
    c = cites[0]
    assert c.temporal_check == "CITED_AFTER_CITING"


def test_degraded_quality_flags() -> None:
    text = "In Swiss Ribbons, (2019) 4 SCC 17 at para 20."
    # Low OCR confidence
    cites_low_ocr = extract_citations_from_anchor(
        anchor_id="wrk_test/en#p10",
        text=text,
        ocr_conf=0.75,
        is_hidden=False,
    )
    assert len(cites_low_ocr) == 1
    assert cites_low_ocr[0].degraded_quality is True
    assert "LOW_OCR_CONF" in cites_low_ocr[0].quality_reasons

    # Hidden text flag
    cites_hidden = extract_citations_from_anchor(
        anchor_id="wrk_test/en#p11",
        text=text,
        ocr_conf=0.99,
        is_hidden=True,
    )
    assert len(cites_hidden) == 1
    assert cites_hidden[0].degraded_quality is True
    assert "HIDDEN_TEXT" in cites_hidden[0].quality_reasons
