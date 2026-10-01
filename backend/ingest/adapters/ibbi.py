"""IBBI Order Mirror Adapter.

Normative sources:
- docs/mvp/01_corporate_corpus_and_sources.md §2.4 (IBBI order mirror)
- docs/02_P0_source_acquisition.md §5.5 (Adapter plug-in contract)
- Session S04 Directive #6: source_record_key = section + PDF file stem.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import structlog
from bs4 import BeautifulSoup, Tag

from ingest.adapters.base import BaseListingAdapter, ListingItem

logger = structlog.get_logger(__name__)

CAPTCHA_SIGNATURES: frozenset[str] = frozenset(
    {
        "securimage",
        "hcaptcha",
        "g-recaptcha",
        "recaptcha",
        "captchainput",
        "captcha_word",
        "human visitor",
        "verify you are human",
        "enter the characters shown",
    }
)

SECTION_PATHS: dict[str, str] = {
    "nclt": "/orders/nclt",
    "nclat": "/orders/nclat",
    "supreme-court": "/orders/supreme-court",
    "high-courts": "/orders/high-courts",
}


class IBBIAdapter(BaseListingAdapter):
    """Adapter for the IBBI orders mirror (/orders/nclt, /nclat, /supreme-court, /high-courts)."""

    adapter_id = "ibbi_orders"
    version = "1.0.0"
    source_id = "IBBI_ORDERS"
    base_url = "https://ibbi.gov.in"

    def build_page_url(self, section: str, page_number: int) -> str:
        """Construct URL for IBBI section and page."""
        clean_sec = section.lower().strip()
        path = SECTION_PATHS.get(clean_sec, f"/orders/{clean_sec}")
        if page_number <= 1:
            return urljoin(self.base_url, path)
        return urljoin(self.base_url, f"{path}?page={page_number}")

    def detect_captcha(self, html: str) -> bool:
        """Check for CAPTCHA challenge in HTML markup."""
        lower_html = html.lower()
        for sig in CAPTCHA_SIGNATURES:
            if sig in lower_html:
                logger.warn("captcha_signature_detected", signature=sig)
                return True
        return False

    def detect_layout_drift(self, html: str, items: list[ListingItem]) -> bool:
        """Detect if table format changed or 0 items parsed unexpectedly."""
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="reporttable")
        if not isinstance(table, Tag):
            # Table is missing entirely
            return True

        # Check expected headers
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if not any("order" in h or "date" in h for h in headers):
            return True
        if not any("subject" in h for h in headers):
            return True

        # If table exists with headers but 0 items extracted
        if len(items) == 0:
            tbody = table.find("tbody")
            if isinstance(tbody, Tag) and tbody.find_all("tr"):
                # Rows existed in HTML but 0 items extracted -> parser failed!
                return True

        return False

    def parse_listing_page(self, html: str, section: str, page_number: int) -> list[ListingItem]:
        """Extract order items from IBBI listing HTML."""
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="reporttable")
        if not isinstance(table, Tag):
            return []

        tbody = table.find("tbody")
        if isinstance(tbody, Tag):
            rows = list(tbody.find_all("tr"))
        else:
            rows = list(table.find_all("tr")[1:])

        items: list[ListingItem] = []

        for idx, row in enumerate(rows):
            if not isinstance(row, Tag):
                continue
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            # Expected 4 cols: Sr.No. (0), Orders Date (1), Subject (2), Orders Remarks (3)
            # Or 3 cols if remarks column is omitted
            order_date_str = cols[1].get_text(strip=True) if len(cols) > 1 else ""
            subject_td = cols[2] if len(cols) > 2 else cols[1]
            remarks_str = cols[3].get_text(strip=True) if len(cols) > 3 else ""

            # Extract PDF link from subject column
            if not isinstance(subject_td, Tag):
                continue
            link = subject_td.find("a")
            if not isinstance(link, Tag) or not link.get("href"):
                continue

            raw_href = str(link["href"]).strip()
            # Clean href if it has unquoted attributes attached
            raw_href = raw_href.split()[0]
            pdf_url = urljoin(self.base_url, raw_href)

            # Raw subject text
            subject_text = link.get_text(strip=True)
            # Remove image size label e.g. "(548.55 KB)" from end if present
            clean_subject = re.sub(r"\(\s*[\d\.]+\s*(?:KB|MB)\s*\)$", "", subject_text).strip()

            # Extract case number in brackets e.g. [CP(IB) 188 of 2026]
            case_match = re.search(r"\[(.*?)\]", clean_subject)
            case_number = case_match.group(1).strip() if case_match else ""

            # Extract bench from case number or text
            bench = ""
            if "MB" in clean_subject or "Mumbai" in clean_subject:
                bench = "Mumbai"
            elif "New Delhi" in clean_subject or "PB" in clean_subject:
                bench = "Principal Bench, New Delhi"
            elif "Chennai" in clean_subject:
                bench = "Chennai"

            # Stable source_record_key = section + PDF file stem (Directive #6)
            parsed_path = urlparse(pdf_url).path
            file_stem = Path(parsed_path).stem
            record_key = f"{section}:{file_stem}"

            source_metadata = {
                "section": section,
                "order_date": order_date_str,
                "subject": clean_subject,
                "case_number": case_number,
                "bench": bench,
                "remarks": remarks_str,
                "pdf_url": pdf_url,
                "file_stem": file_stem,
            }

            items.append(
                ListingItem(
                    record_key=record_key,
                    detail_url=None,
                    file_url=pdf_url,
                    source_metadata=source_metadata,
                    page_number=page_number,
                    row_index=idx,
                )
            )

        return items
