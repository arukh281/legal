"""Tests for statute and provision mention extraction.

Normative sources:
- docs/03_P1_ingestion_parsing.md §5.8
- docs/mvp/03_data_model_and_contracts.md §3.4
- S05b Directives:
  - Sections, subsections, articles
  - In-document definitions (e.g. "hereinafter referred to as the 'Code'")
  - Point-in-time rules
  - Corpus provision resolution: strictly corpus-only ("not in MVP corpus")
  - Zero SQL tables for statute mentions
"""

from datetime import date

import pytest

from parse.citations.statutes import (
    extract_in_document_definitions,
    extract_statute_mentions_from_anchor,
)


@pytest.mark.django_db
def test_extract_explicit_section_and_act() -> None:
    text = "The application was filed under Section 7 of the Insolvency and Bankruptcy Code, 2016."
    mentions = extract_statute_mentions_from_anchor(
        anchor_id="wrk_test/en#p1",
        text=text,
        decision_date=date(2023, 1, 1),
    )
    assert len(mentions) == 1
    m = mentions[0]
    assert m.act_raw == "Insolvency and Bankruptcy Code, 2016"
    assert m.provisions[0]["anchor"] == "sec-7"
    assert m.resolution_status == "not in MVP corpus"
    assert m.resolved_anchor_ids == []
    assert m.pit_rule == "NO_EXPRESSION"
    assert "Section 7 of the Insolvency and Bankruptcy Code, 2016" in m.quote_selector["exact"]


@pytest.mark.django_db
def test_extract_subsection() -> None:
    text = "The Adjudicating Authority referred to Section 9(5)(i) of the IBC."
    mentions = extract_statute_mentions_from_anchor(
        anchor_id="wrk_test/en#p2",
        text=text,
    )
    assert len(mentions) == 1
    m = mentions[0]
    assert m.provisions[0]["anchor"] == "sec-9.5.i"
    assert m.resolution_status == "not in MVP corpus"


@pytest.mark.django_db
def test_extract_in_document_definitions() -> None:
    header = (
        "Proceedings under the Insolvency and Bankruptcy Code, 2016 "
        "(hereinafter referred to as the 'Code') and Companies Act, 2013 (hereinafter 'the Act')."
    )
    defs = extract_in_document_definitions(header)
    assert "CODE" in defs
    assert "Insolvency and Bankruptcy Code" in defs["CODE"]
    assert "ACT" in defs
    assert "Companies Act" in defs["ACT"]

    # Now use these definitions in a later paragraph
    body = "An order of moratorium was passed under Section 14 of the Code."
    mentions = extract_statute_mentions_from_anchor(
        anchor_id="wrk_test/en#p5",
        text=body,
        document_definitions=defs,
    )
    assert len(mentions) == 1
    m = mentions[0]
    assert m.provisions[0]["anchor"] == "sec-14"
    assert "Insolvency and Bankruptcy Code" in m.act_raw


@pytest.mark.django_db
def test_extract_constitution_article() -> None:
    text = "The law laid down by the Hon'ble Supreme Court under Article 141 of the Constitution is binding."
    mentions = extract_statute_mentions_from_anchor(
        anchor_id="wrk_test/en#p8",
        text=text,
    )
    assert len(mentions) == 1
    m = mentions[0]
    assert m.provisions[0]["anchor"] == "art-141"
    assert "Constitution" in m.act_raw
    assert m.resolution_status == "not in MVP corpus"


@pytest.mark.django_db
def test_degraded_statute_mention() -> None:
    text = "Application under Section 7 of the Code."
    mentions = extract_statute_mentions_from_anchor(
        anchor_id="wrk_test/en#p10",
        text=text,
        ocr_conf=0.65,
        is_hidden=False,
    )
    assert len(mentions) == 1
    assert mentions[0].degraded_quality is True
    assert "LOW_OCR_CONF" in mentions[0].quality_reasons
