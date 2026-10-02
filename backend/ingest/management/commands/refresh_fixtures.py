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
            "--section",
            type=str,
            default="nclt",
            choices=["nclt", "nclat", "supreme-court", "high-courts"],
            help="Section to refresh fixtures for (default: nclt)",
        )
        parser.add_argument(
            "--max-sample-pdfs",
            type=int,
            default=2,
            help="Number of sample PDFs to fetch and store as fixtures (default: 2)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        section = options["section"]
        max_pdfs = options["max_sample_pdfs"]

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
