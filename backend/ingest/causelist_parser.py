"""Deterministic PDF parser for NCLT daily cause lists.

Normative sources:
- Session R2: hearings, dates and Today (§2, §3, User Approval & Corrections)
- docs/mvp/03_data_model_and_contracts.md §3.9
- User Correction 1: Fill missing bench from cause list header before comparison.
- User Correction 2: Stable keys across crawl revisions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

import pymupdf
import structlog

from anchor_lib.case_numbers import (
    NormalizedCaseNumber,
    normalize_bench,
    normalize_case_number,
)

logger = structlog.get_logger(__name__)

MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

RE_BENCH = re.compile(
    r"\b(MUMBAI|NEW\s+DELHI|DELHI|CHENNAI|KOLKATA|AHMEDABAD|HYDERABAD|BENGALURU|BANGALORE|"
    r"CHANDIGARH|ALLAHABAD|PRAYAGRAJ|CUTTACK|GUWAHATI|JAIPUR|KOCHI|COCHIN|INDORE|AMRITSAR|AMRAVATI)\s*(?:BENCH)?\b",
    re.IGNORECASE,
)

RE_COURT_NO = re.compile(
    r"\b(?:COURT\s*(?:NO\.?|-)?\s*|COURT\s+ROOM\s+(?:NO\.?|-)?\s*)([IVXLCDM\d]+)\b",
    re.IGNORECASE,
)

RE_DATE_NUMERIC = re.compile(
    r"\b(\d{1,2})[\.\/\-](\d{1,2})[\.\/\-](\d{4})\b"
)

RE_DATE_ISO = re.compile(
    r"\b(\d{4})[\.\/\-](\d{1,2})[\.\/\-](\d{1,2})\b"
)

RE_DATE_TEXTUAL = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b",
    re.IGNORECASE,
)

ROMAN_NUMS = {
    "I": "1", "II": "2", "III": "3", "IV": "4", "V": "5",
    "VI": "6", "VII": "7", "VIII": "8", "IX": "9", "X": "10",
}


def _clean_court_no(raw: str) -> str:
    cleaned = raw.strip().upper()
    return ROMAN_NUMS.get(cleaned, cleaned)


@dataclass
class CauseListItem:
    """A single listing row in a court cause list."""

    item_no: str
    case_refs: list[str]
    normalized_cases: list[NormalizedCaseNumber]
    parties: str
    purpose: str
    court_no: str
    bench: str | None
    list_date: date
    section: str | None = None
    remarks: str | None = None
    raw_text: str = ""


@dataclass
class ParsedCauseList:
    """Complete parsed output of a cause list PDF."""

    bench: str | None
    court_no: str
    list_date: date | None
    items: list[CauseListItem] = field(default_factory=list)
    unparsed_lines_count: int = 0
    layout_drift: bool = False
    drift_reason: str | None = None
    total_pages: int = 0


def parse_date_string(text: str) -> date | None:
    """Extract date from string using numeric (DD/MM/YYYY or YYYY-MM-DD) or textual formats."""
    m_iso = RE_DATE_ISO.search(text)
    if m_iso:
        year, month, day = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        try:
            return date(year, month, day)
        except ValueError:
            pass

    m_num = RE_DATE_NUMERIC.search(text)
    if m_num:
        day, month, year = int(m_num.group(1)), int(m_num.group(2)), int(m_num.group(3))
        # Swap if month > 12 (e.g. MM/DD/YYYY)
        if month > 12 and day <= 12:
            day, month = month, day
        try:
            return date(year, month, day)
        except ValueError:
            pass

    m_text = RE_DATE_TEXTUAL.search(text)
    if m_text:
        day = int(m_text.group(1))
        month_str = m_text.group(2).lower()
        m_val = MONTH_MAP.get(month_str)
        year = int(m_text.group(3))
        if m_val is not None:
            try:
                return date(year, m_val, day)
            except ValueError:
                pass
    return None


class NCLTCauseListParser:
    """Deterministic parser for NCLT daily cause list PDFs."""

    def parse_pdf_bytes(self, pdf_bytes: bytes, fallback_date: date | None = None) -> ParsedCauseList:
        """Parse NCLT cause list PDF bytes into structured items."""
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")  # type: ignore[no-untyped-call]
        total_pages = len(doc)
        if total_pages == 0:
            return ParsedCauseList(
                bench=None,
                court_no="1",
                list_date=fallback_date,
                layout_drift=True,
                drift_reason="EMPTY_PDF_NO_PAGES",
                total_pages=0,
            )

        # 1. Parse header from page 0
        p0 = doc[0]
        p0_text = re.sub(r"\b([A-Za-z]{1,2})\n\s*([A-Za-z]{2,})\b", r"\1\2", p0.get_text())  # type: ignore[no-untyped-call]

        bench = None
        court_no = "1"
        list_date = None

        m_bench = RE_BENCH.search(p0_text)
        if m_bench:
            bench = normalize_bench(m_bench.group(1))

        m_court = RE_COURT_NO.search(p0_text)
        if m_court:
            court_no = _clean_court_no(m_court.group(1))

        list_date = parse_date_string(p0_text) or fallback_date

        items: list[CauseListItem] = []
        unparsed_lines = 0

        current_main_item: str | None = None
        current_main_case: str | None = None
        current_main_parties: str | None = None

        # 2. Extract tables across pages
        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_text = re.sub(r"\b([A-Za-z]{1,2})\n\s*([A-Za-z]{2,})\b", r"\1\2", page.get_text())  # type: ignore[no-untyped-call]

            # If bench or court_no or date wasn't found on page 0, check other pages
            if not bench:
                m_b = RE_BENCH.search(page_text)
                if m_b:
                    bench = normalize_bench(m_b.group(1))
            if not list_date:
                list_date = parse_date_string(page_text) or fallback_date

            tables = page.find_tables()  # type: ignore[no-untyped-call]
            if tables.tables:
                for table in tables.tables:
                    extracted_rows = table.extract()
                    if not extracted_rows:
                        continue

                    # Determine column map from header row
                    col_map: dict[str, int] = {
                        "item_no": 0,
                        "cp_no": 1,
                        "ia_no": 2,
                        "purpose": 3,
                        "section": 4,
                        "parties": 5,
                    }
                    data_rows_start = 0

                    for r_idx, row in enumerate(extracted_rows[:4]):
                        row_str = " ".join([str(c or "").strip().lower() for c in row])
                        if any(k in row_str for k in ["sr", "s.no", "sl.no", "item"]) and any(
                            k in row_str for k in ["cp", "case", "petition", "parties", "ia"]
                        ):
                            for c_idx, cell in enumerate(row):
                                val = str(cell or "").strip().lower()
                                if any(k in val for k in ["sr", "s.no", "sl.no", "item"]):
                                    col_map["item_no"] = c_idx
                                elif any(k in val for k in ["cp", "petition", "case no"]) and "ia" not in val:
                                    col_map["cp_no"] = c_idx
                                elif any(k in val for k in ["ia", "ca no", "application"]):
                                    col_map["ia_no"] = c_idx
                                elif any(k in val for k in ["purpose", "stage"]):
                                    col_map["purpose"] = c_idx
                                elif any(k in val for k in ["section", "sec", "rule"]):
                                    col_map["section"] = c_idx
                                elif any(k in val for k in ["parties", "name"]):
                                    col_map["parties"] = c_idx
                                elif any(k in val for k in ["practitioner", "counsel", "advocate"]):
                                    col_map["counsel"] = c_idx
                                elif any(k in val for k in ["remarks", "coram", "re-notified"]):
                                    col_map["remarks"] = c_idx
                            data_rows_start = r_idx + 1
                            break

                    for row in extracted_rows[data_rows_start:]:
                        if not any(row):
                            continue

                        row_str = " ".join([str(c or "").strip() for c in row])
                        if any(
                            banner in row_str.upper()
                            for banner in [
                                "ORDINARY LIST",
                                "SUPPLEMENTARY LIST",
                                "CORAM:",
                                "NOTE:",
                                "FOR PENDING ADMISSION",
                                "FOR PRONOUNCEMENT",
                            ]
                        ):
                            continue

                        if any(
                            hdr in row_str.lower()
                            for hdr in [
                                "name of parties",
                                "name of the parties",
                                "counsel for",
                                "ia/ca no",
                                "ca/ia no",
                                "cp no",
                                "cp. no",
                            ]
                        ):
                            continue

                        raw_item = str(row[col_map["item_no"]] or "").strip() if col_map["item_no"] < len(row) else ""
                        raw_cp = str(row[col_map["cp_no"]] or "").strip() if col_map["cp_no"] < len(row) else ""
                        raw_ia = (
                            str(row[col_map["ia_no"]] or "").strip()
                            if "ia_no" in col_map and col_map["ia_no"] < len(row)
                            else ""
                        )
                        purpose = (
                            str(row[col_map["purpose"]] or "").strip()
                            if "purpose" in col_map and col_map["purpose"] < len(row)
                            else ""
                        )
                        section_text = (
                            str(row[col_map["section"]] or "").strip()
                            if "section" in col_map and col_map["section"] < len(row)
                            else None
                        )
                        parties = (
                            str(row[col_map["parties"]] or "").strip()
                            if "parties" in col_map and col_map["parties"] < len(row)
                            else ""
                        )
                        remarks = (
                            str(row[col_map["remarks"]] or "").strip()
                            if "remarks" in col_map and col_map["remarks"] < len(row)
                            else None
                        )

                        clean_cp = re.sub(r"\s+", " ", raw_cp).strip()
                        clean_ia = re.sub(r"\s+", " ", raw_ia).strip()

                        m_item = re.match(r"^(\d{1,4})", raw_item)
                        if m_item:
                            it_no = m_item.group(1)
                            # 1. Main case
                            if re.search(r"\b(?:CP|C\.?P\.?|RCP|R\.?C\.?P\.?|CA|Company\s+Petition|Comp\.\s*App)\b", clean_cp, re.IGNORECASE):
                                current_main_item = it_no
                                current_main_case = clean_cp
                                current_main_parties = parties

                                norm_c = normalize_case_number(clean_cp, default_bench=bench)
                                items.append(
                                    CauseListItem(
                                        item_no=it_no,
                                        case_refs=[clean_cp],
                                        normalized_cases=[norm_c],
                                        parties=parties,
                                        purpose=purpose,
                                        court_no=court_no,
                                        bench=bench,
                                        list_date=list_date or date.today(),
                                        section=section_text,
                                        remarks=remarks,
                                        raw_text=f"{it_no} | {clean_cp} | {parties} | {purpose}",
                                    )
                                )

                            # 2. Check if ia_no also has an application in the same row
                            if clean_ia and not any(k in clean_ia.upper() for k in ["MAIN CASE", "NONE", "-"]):
                                if re.search(r"\b(?:IA|C\.?A|CONT\.?A|COMP\.?APPL)\b", clean_ia, re.IGNORECASE):
                                    norm_ia = normalize_case_number(
                                        clean_ia, default_bench=bench, parent_case=current_main_case
                                    )
                                    items.append(
                                        CauseListItem(
                                            item_no=f"{it_no}.1",
                                            case_refs=[clean_ia],
                                            normalized_cases=[norm_ia],
                                            parties=parties or (current_main_parties or ""),
                                            purpose=purpose,
                                            court_no=court_no,
                                            bench=bench,
                                            list_date=list_date or date.today(),
                                            section=section_text,
                                            remarks=remarks,
                                            raw_text=f"{it_no}.1 | {clean_ia} | {parties} | {purpose}",
                                        )
                                    )
                        else:
                            # Sub-row IA under current main case
                            if clean_ia and re.search(r"\b(?:IA|C\.?A|CONT\.?A|COMP\.?APPL)\b", clean_ia, re.IGNORECASE):
                                m_sub = re.search(r"^(\d{1,3})\.?", raw_cp)
                                sub_no = m_sub.group(1) if m_sub else "1"
                                it_no = f"{current_main_item}.{sub_no}" if current_main_item else sub_no
                                norm_ia = normalize_case_number(
                                    clean_ia, default_bench=bench, parent_case=current_main_case
                                )
                                items.append(
                                    CauseListItem(
                                        item_no=it_no,
                                        case_refs=[clean_ia],
                                        normalized_cases=[norm_ia],
                                        parties=parties or (current_main_parties or ""),
                                        purpose=purpose,
                                        court_no=court_no,
                                        bench=bench,
                                        list_date=list_date or date.today(),
                                        section=section_text,
                                        remarks=remarks,
                                        raw_text=f"{it_no} | {clean_ia} | {parties} | {purpose}",
                                    )
                                )
                            elif clean_cp and re.search(r"\b(?:CP|C\.?P\.?|RCP|R\.?C\.?P\.?|CA|Company\s+Petition|Comp\.\s*App)\b", clean_cp, re.IGNORECASE):
                                # Standalone CP row without item number in col 0
                                it_no = str(len(items) + 1)
                                norm_c = normalize_case_number(clean_cp, default_bench=bench)
                                items.append(
                                    CauseListItem(
                                        item_no=it_no,
                                        case_refs=[clean_cp],
                                        normalized_cases=[norm_c],
                                        parties=parties or (current_main_parties or ""),
                                        purpose=purpose,
                                        court_no=court_no,
                                        bench=bench,
                                        list_date=list_date or date.today(),
                                        section=section_text,
                                        remarks=remarks,
                                        raw_text=f"{it_no} | {clean_cp} | {parties} | {purpose}",
                                    )
                                )
                            else:
                                unparsed_lines += 1
            else:
                # Text-based fallback when no bordered table found
                lines = [line_text.strip() for line_text in page_text.splitlines() if line_text.strip()]
                idx = 0
                while idx < len(lines):
                    line = lines[idx]

                    # 1. Single-line row check
                    m_row = re.match(
                        r"^(\d{1,4})\.?\s+((?:CP|IA|CA|RCP|Company\s+Appeal|Comp\.\s*App)[^\n]+?)(?:\s+(For\s+[A-Za-z\s]+|Pronouncement[A-Za-z\s]*))?(?:\s+(.*))?$",
                        line,
                        re.IGNORECASE,
                    )
                    if m_row:
                        item_no = m_row.group(1)
                        case_str = m_row.group(2).strip()
                        purpose_str = (m_row.group(3) or "").strip()
                        rem_str = (m_row.group(4) or "").strip()
                        norm_c = normalize_case_number(case_str, default_bench=bench)
                        items.append(
                            CauseListItem(
                                item_no=item_no,
                                case_refs=[case_str],
                                normalized_cases=[norm_c],
                                parties=rem_str,
                                purpose=purpose_str,
                                court_no=court_no,
                                bench=bench,
                                list_date=list_date or date.today(),
                                raw_text=line,
                            )
                        )
                        idx += 1
                        continue

                    # 2. Sequential multi-line row check (item_no on its own line)
                    m_item = re.match(r"^(\d{1,4})\.?$", line)
                    if m_item and idx + 1 < len(lines):
                        item_no = m_item.group(1)
                        next_line = lines[idx + 1]
                        m_case = re.search(r"\b(?:CP|IA|CA|RCP|Company\s+Appeal|Comp\.\s*App)\b", next_line, re.IGNORECASE)
                        if m_case:
                            case_str = next_line
                            purpose_str = ""
                            parties_str = ""
                            offset = 2
                            if idx + offset < len(lines) and not re.match(r"^\d{1,4}\.?$", lines[idx + offset]):
                                cand = lines[idx + offset]
                                if any(k in cand.lower() for k in ["for ", "pronouncement", "hearing", "admission", "direction", "order"]):
                                    purpose_str = cand
                                    offset += 1
                                    if idx + offset < len(lines) and not re.match(r"^\d{1,4}\.?$", lines[idx + offset]):
                                        parties_str = lines[idx + offset]
                                        offset += 1
                                else:
                                    parties_str = cand
                                    offset += 1

                            norm_c = normalize_case_number(case_str, default_bench=bench)
                            items.append(
                                CauseListItem(
                                item_no=item_no,
                                case_refs=[case_str],
                                normalized_cases=[norm_c],
                                parties=parties_str,
                                purpose=purpose_str,
                                court_no=court_no,
                                bench=bench,
                                list_date=list_date or date.today(),
                                raw_text=f"{item_no} | {case_str} | {purpose_str} | {parties_str}",
                                )
                            )
                            idx += offset
                            continue

                    if any(k in line for k in ["CP (IB)", "IA", "CA (IB)"]):
                        unparsed_lines += 1
                    idx += 1

        # Check layout drift
        layout_drift = False
        drift_reason = None

        has_meaningful_text = len(p0_text.strip()) > 100
        if has_meaningful_text and len(items) == 0:
            layout_drift = True
            drift_reason = "PAGE_TEXT_PRESENT_BUT_ZERO_ITEMS_PARSED"
        elif bench is None:
            layout_drift = True
            drift_reason = "BENCH_HEADER_NOT_DETECTED"
        elif list_date is None:
            layout_drift = True
            drift_reason = "DATE_HEADER_NOT_DETECTED"

        return ParsedCauseList(
            bench=bench,
            court_no=court_no,
            list_date=list_date,
            items=items,
            unparsed_lines_count=unparsed_lines,
            layout_drift=layout_drift,
            drift_reason=drift_reason,
            total_pages=total_pages,
        )
