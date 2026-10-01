"""Tests for IBBI listing adapter against recorded real fixtures.

Normative sources:
- docs/mvp/01_corporate_corpus_and_sources.md §2.4
- Session S04 Directive #6 (source_record_key = section + file stem)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ingest.adapters.ibbi import IBBIAdapter

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "eval" / "fixtures" / "ibbi"


@pytest.fixture
def adapter() -> IBBIAdapter:
    return IBBIAdapter()


def test_ibbi_url_building(adapter: IBBIAdapter) -> None:
    """Verify build_page_url across all 4 sections and pagination."""
    assert adapter.build_page_url("nclt", 1) == "https://ibbi.gov.in/orders/nclt"
    assert adapter.build_page_url("nclt", 2) == "https://ibbi.gov.in/orders/nclt?page=2"
    assert adapter.build_page_url("nclat", 1) == "https://ibbi.gov.in/orders/nclat"
    assert adapter.build_page_url("nclat", 3) == "https://ibbi.gov.in/orders/nclat?page=3"
    assert adapter.build_page_url("supreme-court", 1) == "https://ibbi.gov.in/orders/supreme-court"
    assert adapter.build_page_url("high-courts", 1) == "https://ibbi.gov.in/orders/high-courts"


def test_parse_real_nclt_listing_page_1(adapter: IBBIAdapter) -> None:
    """Parse real recorded NCLT page 1 fixture."""
    html_path = FIXTURES_DIR / "nclt_page1.html"
    assert html_path.exists(), f"Fixture missing: {html_path}"

    html = html_path.read_text(encoding="utf-8")
    items = adapter.parse_listing_page(html, section="nclt", page_number=1)

    assert len(items) == 20, f"Expected 20 rows, got {len(items)}"

    # First item verification
    first = items[0]
    assert first.page_number == 1
    assert first.row_index == 0
    assert first.file_url.startswith("https://ibbi.gov.in/uploads/order/")
    assert first.file_url.endswith(".pdf")

    # Directive #6: record_key must be section + file stem (never order date or case number)
    file_stem = Path(first.file_url).stem
    assert first.record_key == f"nclt:{file_stem}"

    # Metadata verification
    meta = first.source_metadata
    assert meta["section"] == "nclt"
    assert "TAKSHASHILA" in meta["subject"]
    assert "CP(IB)" in meta["case_number"]
    assert "Admission" in meta["remarks"]
    assert meta["file_stem"] == file_stem


def test_parse_real_nclt_listing_page_2(adapter: IBBIAdapter) -> None:
    """Parse real recorded NCLT page 2 fixture."""
    html_path = FIXTURES_DIR / "nclt_page2.html"
    assert html_path.exists(), f"Fixture missing: {html_path}"

    html = html_path.read_text(encoding="utf-8")
    items = adapter.parse_listing_page(html, section="nclt", page_number=2)

    assert len(items) == 20
    for item in items:
        assert item.page_number == 2
        assert item.record_key.startswith("nclt:")
        assert item.file_url.endswith(".pdf")


def test_detect_captcha(adapter: IBBIAdapter) -> None:
    """CAPTCHA signature detection returns True on challenge markup and False on normal page."""
    captcha_html = (FIXTURES_DIR / "captcha_page.html").read_text(encoding="utf-8")
    normal_html = (FIXTURES_DIR / "nclt_page1.html").read_text(encoding="utf-8")

    assert adapter.detect_captcha(captcha_html) is True
    assert adapter.detect_captcha(normal_html) is False


def test_detect_layout_drift(adapter: IBBIAdapter) -> None:
    """Layout drift detection detects missing table and 0 items on valid table."""
    corrupt_html = (FIXTURES_DIR / "corrupt_listing.html").read_text(encoding="utf-8")
    normal_html = (FIXTURES_DIR / "nclt_page1.html").read_text(encoding="utf-8")

    # Corrupt HTML has no table -> drift!
    assert adapter.detect_layout_drift(corrupt_html, items=[]) is True

    # Normal HTML with parsed items -> no drift!
    items = adapter.parse_listing_page(normal_html, section="nclt", page_number=1)
    assert adapter.detect_layout_drift(normal_html, items=items) is False

    # Normal HTML with 0 items (e.g. selector broke) -> drift!
    assert adapter.detect_layout_drift(normal_html, items=[]) is True
