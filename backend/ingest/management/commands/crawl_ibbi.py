"""Management command to run an IBBI crawl.

Normative source:
- Session S04 Directive #8: A management command to run a small real crawl manually (e.g. --section nclt --pages 2).
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from ingest.adapters.ibbi import IBBIAdapter
from ingest.crawler import SourceCrawler


class Command(BaseCommand):
    help = "Crawl IBBI orders mirror across sections (nclt, nclat, supreme-court, high-courts, all)"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--section",
            type=str,
            default="nclt",
            choices=["nclt", "nclat", "supreme-court", "high-courts", "all"],
            help="Section to crawl (default: nclt)",
        )
        parser.add_argument(
            "--pages",
            type=int,
            default=2,
            help="Maximum pages to crawl per section (default: 2)",
        )
        parser.add_argument(
            "--mode",
            type=str,
            default="delta",
            choices=["delta", "backfill"],
            help="Crawl mode: delta (newest pages until N unchanged) or backfill (night IST)",
        )
        parser.add_argument(
            "--crawl-run-id",
            type=str,
            default=None,
            help="Resume an existing crawl run by ID",
        )
        parser.add_argument(
            "--stop-on-unchanged",
            type=int,
            default=20,
            help="Stop delta run after N consecutive unchanged records (default: 20)",
        )
        parser.add_argument(
            "--offline",
            action="store_true",
            help="Run against recorded offline fixtures rather than live network",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        section_arg: str = options["section"]
        max_pages: int = options["pages"]
        mode: str = options["mode"]
        crawl_run_id: str | None = options["crawl_run_id"]
        stop_on_unchanged: int = options["stop_on_unchanged"]

        sections = (
            ["nclt", "nclat", "supreme-court", "high-courts"]
            if section_arg == "all"
            else [section_arg]
        )

        resolver = None
        if options.get("offline", False):
            from pathlib import Path

            from django.conf import settings

            from core.http_client import RawHttpResponse

            fixtures_dir = Path(settings.BASE_DIR).parent / "eval" / "fixtures" / "ibbi"
            p1 = (fixtures_dir / "nclt_page1.html").read_text(encoding="utf-8")
            p2 = (fixtures_dir / "nclt_page2.html").read_text(encoding="utf-8")
            sample_pdf = (fixtures_dir / "sample_order_1.pdf").read_bytes()

            def _resolver(url: str) -> RawHttpResponse | None:
                if "page=2" in url:
                    return RawHttpResponse(
                        200, {"content-type": "text/html"}, p2.encode("utf-8"), url
                    )
                elif "/orders/" in url:
                    return RawHttpResponse(
                        200, {"content-type": "text/html"}, p1.encode("utf-8"), url
                    )
                elif url.endswith(".pdf"):
                    return RawHttpResponse(
                        200, {"content-type": "application/pdf"}, sample_pdf, url
                    )
                return None

            resolver = _resolver

        adapter = IBBIAdapter()
        crawler = SourceCrawler(adapter=adapter, offline_fixture_resolver=resolver)

        self.stdout.write(
            f"Starting IBBI crawl on sections={sections}, pages={max_pages}, mode={mode}..."
        )

        for sec in sections:
            self.stdout.write(f"\n--- Crawling Section: {sec} ---")
            summary = crawler.crawl_section(
                section=sec,
                mode=mode,
                max_pages=max_pages,
                crawl_run_id=crawl_run_id,
                stop_on_unchanged_count=stop_on_unchanged,
            )

            spacing_str = (
                f"min={summary.min_request_interval_s:.2f}s, "
                f"avg={summary.avg_request_interval_s:.2f}s, "
                f"max={summary.max_request_interval_s:.2f}s"
                if summary.min_request_interval_s is not None
                and summary.avg_request_interval_s is not None
                and summary.max_request_interval_s is not None
                else "N/A"
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n=== Section '{sec}' Report ===\n"
                    f"  Status: {summary.status}\n"
                    f"  Pages crawled: {summary.pages_crawled}\n"
                    f"  Rows parsed: {summary.items_total}\n"
                    f"  PDFs downloaded: {summary.pdf_downloads_count}\n"
                    f"  Captures by change_kind: NEW={summary.new_count}, "
                    f"UNCHANGED={summary.unchanged_count}, CHANGED={summary.changed_count}, "
                    f"METADATA_CHANGED={summary.metadata_changed_count}\n"
                    f"  Profile ID in fetch_context: {summary.observed_profile_id or 'N/A'}\n"
                    f"  Observed rate-limit spacing: {spacing_str}"
                )
            )
