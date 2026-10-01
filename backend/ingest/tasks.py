"""Procrastinate tasks for background crawl runs.

Normative source:
- docs/mvp/03_data_model_and_contracts.md §3.16, §5
"""

from __future__ import annotations

from typing import Any

from procrastinate.contrib.django import app

from ingest.adapters.ibbi import IBBIAdapter
from ingest.crawler import SourceCrawler


@app.task(queue="bulk")
def crawl_ibbi_section_task(
    section: str,
    mode: str = "delta",
    max_pages: int | None = None,
    crawl_run_id: str | None = None,
) -> dict[str, Any]:
    """Background task executing an IBBI crawl across a section."""
    adapter = IBBIAdapter()
    crawler = SourceCrawler(adapter=adapter)
    summary = crawler.crawl_section(
        section=section,
        mode=mode,
        max_pages=max_pages,
        crawl_run_id=crawl_run_id,
    )
    return {
        "crawl_run_id": summary.crawl_run_id,
        "source_id": summary.source_id,
        "section": summary.section,
        "status": summary.status,
        "pages_crawled": summary.pages_crawled,
        "items_total": summary.items_total,
        "new_count": summary.new_count,
        "unchanged_count": summary.unchanged_count,
        "changed_count": summary.changed_count,
    }
