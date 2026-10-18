"""Management command to refresh test fixtures strictly through GatedHttpClient.

Normative source:
- Session S04 Closure Directive #3: From now on, any fetch from a source,
  including fixture refreshes, goes through the gated client.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand

from ingest.adapters.ibbi import IBBIAdapter
from ingest.gate import GatedHttpClient


class Command(BaseCommand):
    help = "Refresh IBBI evaluation fixtures strictly via GatedHttpClient"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--source",
            type=str,
            default="ibbi",
            choices=["ibbi", "nclt_causelist"],
            help="Source to refresh fixtures for (default: ibbi)",
        )
        parser.add_argument(
            "--section",
            type=str,
            default="nclt",
            choices=["nclt", "nclat", "supreme-court", "high-courts"],
            help="Section for IBBI (default: nclt)",
        )
        parser.add_argument(
            "--max-sample-pdfs",
            type=int,
            default=4,
            help="Number of sample PDFs to fetch and store as fixtures (default: 4)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        source = options["source"]
        max_pdfs = options["max_sample_pdfs"]

        if source == "nclt_causelist":
            self.refresh_nclt_causelists(max_pdfs=max_pdfs)
            return

        section = options["section"]
        fixtures_dir = Path(settings.BASE_DIR).parent / "eval" / "fixtures" / "ibbi"
        fixtures_dir.mkdir(parents=True, exist_ok=True)

        adapter = IBBIAdapter()
        client = GatedHttpClient(source_id="IBBI_ORDERS", crawl_mode="delta")

        self.stdout.write(
            f"Refreshing fixtures for '{section}' strictly through GatedHttpClient (rate limit ≥ 3.0s)..."
        )

        # 1. Fetch Page 1 HTML
        url_p1 = adapter.build_page_url(section=section, page_number=1)
        self.stdout.write(f"Fetching page 1: {url_p1}...")
        resp_p1 = client.get(url_p1)
        if resp_p1.status_code != 200:
            self.stderr.write(f"Failed to fetch page 1: HTTP {resp_p1.status_code}")
            return
        p1_path = fixtures_dir / f"{section}_page1.html"
        p1_path.write_bytes(resp_p1.content)
        self.stdout.write(f"Saved page 1 HTML ({len(resp_p1.content)} bytes) -> {p1_path}")

        # 2. Fetch Page 2 HTML
        url_p2 = adapter.build_page_url(section=section, page_number=2)
        self.stdout.write(f"Fetching page 2: {url_p2}...")
        resp_p2 = client.get(url_p2)
        if resp_p2.status_code != 200:
            self.stderr.write(f"Failed to fetch page 2: HTTP {resp_p2.status_code}")
            return
        p2_path = fixtures_dir / f"{section}_page2.html"
        p2_path.write_bytes(resp_p2.content)
        self.stdout.write(f"Saved page 2 HTML ({len(resp_p2.content)} bytes) -> {p2_path}")

        # 3. Parse Page 1 items to find sample PDFs
        items = adapter.parse_listing_page(resp_p1.text, section=section, page_number=1)
        pdf_urls = [item.file_url for item in items if item.file_url][:max_pdfs]

        for idx, pdf_url in enumerate(pdf_urls, start=1):
            self.stdout.write(f"Fetching sample PDF {idx}/{len(pdf_urls)}: {pdf_url}...")
            resp_pdf = client.get(pdf_url)
            if resp_pdf.status_code == 200:
                pdf_path = fixtures_dir / f"sample_order_{idx}.pdf"
                pdf_path.write_bytes(resp_pdf.content)
                self.stdout.write(f"Saved sample PDF ({len(resp_pdf.content)} bytes) -> {pdf_path}")
            else:
                self.stderr.write(f"Failed to fetch PDF: HTTP {resp_pdf.status_code}")

        min_int = client.min_observed_interval
        avg_int = client.avg_observed_interval
        max_int = client.max_observed_interval
        spacing_str = (
            f"min={min_int:.2f}s, avg={avg_int:.2f}s, max={max_int:.2f}s"
            if min_int is not None and avg_int is not None and max_int is not None
            else "N/A"
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully refreshed fixtures for '{section}'. "
                f"Observed rate-limit spacing across {len(client.observed_intervals)} requests: {spacing_str}."
            )
        )

    def refresh_nclt_causelists(self, max_pdfs: int = 4) -> None:
        import json
        import urllib.parse

        from bs4 import BeautifulSoup

        fixtures_dir = Path(settings.BASE_DIR).parent / "eval" / "fixtures" / "nclt_causelist"
        fixtures_dir.mkdir(parents=True, exist_ok=True)

        client = GatedHttpClient(source_id="NCLT_CAUSELIST", crawl_mode="delta")
        listing_url = "https://nclt.gov.in/all-cause-list"

        self.stdout.write(
            "Refreshing NCLT cause-list fixtures strictly through GatedHttpClient (rate limit ≥ 3.0s)..."
        )
        self.stdout.write(f"Fetching cause list table: {listing_url}...")
        resp = client.get(listing_url)
        if resp.status_code != 200:
            self.stderr.write(f"Failed to fetch {listing_url}: HTTP {resp.status_code}")
            return

        # Check for CAPTCHA (Non-negotiable #5)
        if "captcha" in resp.text.lower() and "recaptcha" in resp.text.lower():
            raise RuntimeError("CAPTCHA detected on NCLT cause list page. Aborting.")

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if not table or not hasattr(table, "find_all"):
            self.stderr.write("No table found on all-cause-list page.")
            return

        records: list[dict[str, Any]] = []
        rows = table.find_all("tr")[1:]  # skip header
        for tr in rows:
            tds = [td.text.strip() for td in tr.find_all("td")]
            a = tr.find("a")
            if not a or not a.get("href"):
                continue
            href = a["href"]
            if not href.lower().endswith(".pdf"):
                continue

            full_url = urllib.parse.urljoin("https://nclt.gov.in", href)
            title = tds[1] if len(tds) > 1 else ""
            court = tds[2] if len(tds) > 2 else ""
            entries = tds[3] if len(tds) > 3 else ""
            list_date = tds[4] if len(tds) > 4 else ""

            records.append({
                "title": title,
                "court": court,
                "entries": entries,
                "date": list_date,
                "url": full_url,
            })

        self.stdout.write(f"Found {len(records)} cause list PDF links on table.")
        target_records = records[:max_pdfs]
        saved_manifest: list[dict[str, Any]] = []

        for idx, rec in enumerate(target_records, start=1):
            pdf_url = rec["url"]
            self.stdout.write(f"Fetching sample NCLT PDF {idx}/{len(target_records)}: {pdf_url}...")
            pdf_resp = client.get(pdf_url)
            if pdf_resp.status_code == 200:
                filename = f"nclt_causelist_{idx}.pdf"
                dest_path = fixtures_dir / filename
                dest_path.write_bytes(pdf_resp.content)
                self.stdout.write(f"Saved {filename} ({len(pdf_resp.content)} bytes) -> {dest_path}")
                saved_manifest.append({
                    "filename": filename,
                    "title": rec["title"],
                    "court": rec["court"],
                    "entries": rec["entries"],
                    "date": rec["date"],
                    "url": rec["url"],
                    "size_bytes": len(pdf_resp.content),
                })
            else:
                self.stderr.write(f"Failed to fetch PDF: HTTP {pdf_resp.status_code}")

        manifest_path = fixtures_dir / "manifest.json"
        manifest_path.write_text(json.dumps(saved_manifest, indent=2))
        self.stdout.write(f"Saved manifest -> {manifest_path}")

        min_int = client.min_observed_interval
        avg_int = client.avg_observed_interval
        max_int = client.max_observed_interval
        spacing_str = (
            f"min={min_int:.2f}s, avg={avg_int:.2f}s, max={max_int:.2f}s"
            if min_int is not None and avg_int is not None and max_int is not None
            else "N/A"
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully refreshed {len(saved_manifest)} NCLT cause list fixtures. "
                f"Observed rate-limit spacing across {len(client.observed_intervals)} requests: {spacing_str}."
            )
        )

