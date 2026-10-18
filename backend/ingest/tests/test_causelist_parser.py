"""Tests for NCLT deterministic cause-list parser."""

from datetime import date

import pymupdf

from ingest.causelist_parser import NCLTCauseListParser, parse_date_string


def make_sample_causelist_pdf(
    bench: str = "MUMBAI BENCH",
    court: str = "COURT NO. 1",
    date_str: str = "20.10.2026",
    items: list[tuple[str, str, str, str]] | None = None,
) -> bytes:
    """Generate an in-memory PDF with header and structured table."""
    if items is None:
        items = [
            ("1", "CP (IB) 188/2026", "For Admission", "State Bank of India V/s ABC Infra Ltd"),
            ("2", "IA 456/2026 in CP (IB) 123/MB/2026", "For Hearing", "XYZ Financial Services Vs PQR Ltd"),
            ("3", "RCP (IB) 55/MB/2026", "Pronouncement of Order", "Bank of Baroda Vs Solvents Ltd"),
        ]

    doc = pymupdf.open()  # type: ignore[no-untyped-call]
    page = doc.new_page(width=595, height=842)  # A4

    # Add header
    header_text = (
        f"NATIONAL COMPANY LAW TRIBUNAL\n"
        f"{bench}\n"
        f"{court}\n"
        f"DAILY CAUSE LIST\n"
        f"DATE: {date_str}\n"
        f"TIME: 10:30 AM\n"
    )
    page.insert_text((50, 50), header_text, fontsize=11)

    # Draw table borders and text
    y_start = 160
    row_height = 30
    col_x = [50, 90, 270, 370, 545]

    # Draw header row
    headers = ["S.No.", "CP / CA / IA No.", "Purpose", "Name of Parties"]
    page.draw_rect(pymupdf.Rect(50, y_start, 545, y_start + row_height), color=(0, 0, 0), width=1)  # type: ignore[no-untyped-call]
    for i, h in enumerate(headers):
        page.insert_text((col_x[i] + 5, y_start + 18), h, fontsize=9)

    cur_y = y_start + row_height
    for item in items:
        page.draw_rect(pymupdf.Rect(50, cur_y, 545, cur_y + row_height), color=(0, 0, 0), width=0.5)  # type: ignore[no-untyped-call]
        for i, val in enumerate(item):
            page.insert_text((col_x[i] + 5, cur_y + 18), val, fontsize=8)
        cur_y += row_height

    raw_bytes: bytes = doc.tobytes()  # type: ignore[no-untyped-call]
    return raw_bytes


def test_parse_date_string() -> None:
    assert parse_date_string("DATE: 20.10.2026") == date(2026, 10, 20)
    assert parse_date_string("Hearing on 5th November 2026") == date(2026, 11, 5)
    assert parse_date_string("List for 2026-12-01") == date(2026, 12, 1)


def test_causelist_parser_standard_table() -> None:
    pdf_bytes = make_sample_causelist_pdf()
    parser = NCLTCauseListParser()
    result = parser.parse_pdf_bytes(pdf_bytes)

    assert result.layout_drift is False
    assert result.bench == "MUM"
    assert result.court_no == "1"
    assert result.list_date == date(2026, 10, 20)
    assert len(result.items) == 3

    # Check item 1: bench filled from header (Correction 1)
    item1 = result.items[0]
    assert item1.item_no == "1"
    assert len(item1.normalized_cases) == 1
    norm1 = item1.normalized_cases[0]
    assert norm1.case_type == "CP (IB)"
    assert norm1.case_number == "188"
    assert norm1.bench == "MUM"  # Missing bench filled from header!
    assert norm1.year == 2026
    assert norm1.canonical == "CP (IB) 188/MUM/2026"

    # Check item 2: parent case extracted
    item2 = result.items[1]
    assert item2.item_no == "2"
    norm2 = item2.normalized_cases[0]
    assert norm2.parent_case_type == "CP (IB)"
    assert norm2.parent_case_number == "123"
    assert norm2.parent_bench == "MUM"
    assert norm2.parent_year == 2026

    # Check item 3: RCP (IB) distinct from CP (IB)
    item3 = result.items[2]
    assert item3.normalized_cases[0].case_type == "RCP (IB)"


def test_causelist_parser_drift_detection() -> None:
    """PDF with no bench or date header reports layout drift."""
    doc = pymupdf.open()  # type: ignore[no-untyped-call]
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Some random unstructured court notice without any bench name", fontsize=12)
    pdf_bytes: bytes = doc.tobytes()  # type: ignore[no-untyped-call]

    parser = NCLTCauseListParser()
    result = parser.parse_pdf_bytes(pdf_bytes)
    assert result.layout_drift is True
    assert result.drift_reason in ("BENCH_HEADER_NOT_DETECTED", "DATE_HEADER_NOT_DETECTED", "PAGE_TEXT_PRESENT_BUT_ZERO_ITEMS_PARSED")


def test_real_nclt_fixtures_golden() -> None:
    """Golden tests on real public NCLT cause-list PDFs."""
    from pathlib import Path

    from django.conf import settings

    fixtures_dir = Path(settings.BASE_DIR).parent / "eval" / "fixtures" / "nclt_causelist"
    if not fixtures_dir.exists():
        return

    parser = NCLTCauseListParser()

    # Fixture 1: Mumbai Bench Court-IV
    f1 = fixtures_dir / "nclt_causelist_1.pdf"
    if f1.exists():
        res1 = parser.parse_pdf_bytes(f1.read_bytes())
        assert res1.layout_drift is False
        assert res1.bench == "MUM"
        assert res1.court_no == "4"
        assert res1.list_date == date(2026, 10, 21)
        assert len(res1.items) >= 40
        # Check main case and child IA with parent case
        item101 = next(it for it in res1.items if it.item_no == "101")
        assert any(c.case_number == "736" and c.case_type == "CP (IB)" for c in item101.normalized_cases)
        item101_1 = next(it for it in res1.items if it.item_no == "101.1")
        assert any(c.parent_case_number == "736" and c.parent_case_type == "CP (IB)" for c in item101_1.normalized_cases)

    # Fixture 2: Chandigarh Bench Court-II
    f2 = fixtures_dir / "nclt_causelist_2.pdf"
    if f2.exists():
        res2 = parser.parse_pdf_bytes(f2.read_bytes())
        assert res2.layout_drift is False
        assert res2.bench == "CHD"
        assert res2.court_no == "2"
        assert res2.list_date == date(2026, 10, 21)
        assert len(res2.items) >= 30
        item101 = next(it for it in res2.items if it.item_no == "101")
        assert any(c.case_number == "5" and c.bench == "CHD" for c in item101.normalized_cases)

    # Fixture 3: Mumbai Bench Court-III
    f3 = fixtures_dir / "nclt_causelist_3.pdf"
    if f3.exists():
        res3 = parser.parse_pdf_bytes(f3.read_bytes())
        assert res3.layout_drift is False
        assert res3.bench == "MUM"
        assert res3.court_no == "3"
        assert res3.list_date == date(2026, 10, 21)
        assert len(res3.items) >= 40

    # Fixture 4: Mumbai Bench Court-I
    f4 = fixtures_dir / "nclt_causelist_4.pdf"
    if f4.exists():
        res4 = parser.parse_pdf_bytes(f4.read_bytes())
        assert res4.layout_drift is False
        assert res4.bench == "MUM"
        assert res4.court_no == "1"
        assert res4.list_date == date(2026, 10, 21)
        assert len(res4.items) >= 40
        # Check child IA parent case
        item1_1 = next(it for it in res4.items if it.item_no == "1.1")
        assert any(c.parent_case_number == "1049" and c.parent_case_type == "CP (IB)" for c in item1_1.normalized_cases)

