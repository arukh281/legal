"""NCLT Daily Cause List Adapter and Crawler.

Normative sources:
- Session R2: hearings, dates and Today (§2, §3, User Approval & Corrections)
- docs/mvp/01_corporate_corpus_and_sources.md §6.2
- docs/mvp/03_data_model_and_contracts.md §3.9, §4
- User Correction 1: Fill missing bench from header before comparison.
- User Correction 2: Stable keys across revisions.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

import structlog
from django.db import transaction

from anchor_lib.ids import mint_id
from ingest.causelist_parser import NCLTCauseListParser, ParsedCauseList
from ingest.gate import GatedHttpClient
from ingest.models import Capture
from ingest.storage import BlobStorage
from ops.outbox import publish_event

logger = structlog.get_logger(__name__)


@dataclass
class CauseListCrawlSummary:
    """Metrics from a cause list crawl run."""

    crawl_run_id: str
    source_id: str
    lists_crawled: int
    items_parsed: int
    drifted_count: int
    published_events_count: int
    status: str
    error: str | None = None


class NCLTCauseListAdapter:
    """Adapter for NCLT daily cause lists."""

    adapter_id = "nclt_causelist"
    version = "1.0.0"
    source_id = "NCLT_CAUSELIST"
    base_url = "https://nclt.gov.in"

    def __init__(
        self,
        *,
        storage: BlobStorage | None = None,
        gated_client: GatedHttpClient | None = None,
        offline_fixture_resolver: Callable[[str], Any] | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self.storage = storage or BlobStorage()
        self.offline_fixture_resolver = offline_fixture_resolver
        self.now_fn = now_fn or (lambda: datetime.now(UTC))
        self._gated_client = gated_client
        self.parser = NCLTCauseListParser()

    def _get_client(self) -> GatedHttpClient:
        if self._gated_client is not None:
            return self._gated_client
        return GatedHttpClient(
            source_id=self.source_id,
            access_mode="OPEN",
            crawl_mode="delta",
            offline_fixture_resolver=self.offline_fixture_resolver,
            now_fn=self.now_fn,
        )

    def process_causelist_pdf(
        self,
        pdf_bytes: bytes,
        source_url: str,
        *,
        crawl_run_id: str | None = None,
        fallback_date: date | None = None,
    ) -> ParsedCauseList:
        """Parse a cause-list PDF, store its raw bytes in CAS, and publish court.causelist.published.v1."""
        now = self.now_fn()
        parsed = self.parser.parse_pdf_bytes(pdf_bytes, fallback_date=fallback_date)

        # Store raw blob in CAS
        raw_id, _, _ = self.storage.store_blob(
            pdf_bytes,
            content_type="application/pdf",
            first_seen_at=now,
        )

        bench_code = parsed.bench or "UNKNOWN"
        court_no = parsed.court_no
        list_date_str = parsed.list_date.isoformat() if parsed.list_date else date.today().isoformat()
        record_key = f"{bench_code}_{court_no}_{list_date_str}"

        with transaction.atomic():
            # 1. Record capture in plc.capture
            Capture.objects.create(
                capture_id=mint_id("cap"),
                source_id=self.source_id,
                source_record_key=record_key,
                url=source_url,
                fetched_at=now,
                change_kind="NEW",
                raw_id=raw_id,
                rights_class="OFFICIAL",
                provenance_tier="OFFICIAL_GOVERNMENT",
                fetch_context={
                    "bench": bench_code,
                    "court_no": court_no,
                    "list_date": list_date_str,
                    "items_count": len(parsed.items),
                    "layout_drift": parsed.layout_drift,
                },
                crawl_run_id=crawl_run_id,
            )

            # 2. Publish court.causelist.published.v1 event
            causelist_event_data = {
                "source_id": self.source_id,
                "raw_id": raw_id,
                "bench": bench_code,
                "court_no": court_no,
                "list_date": list_date_str,
                "items": [
                    {
                        "item_no": it.item_no,
                        "case_refs": it.case_refs,
                        "normalized_cases": [
                            {
                                "raw": c.raw,
                                "case_type": c.case_type,
                                "case_number": c.case_number,
                                "year": c.year,
                                "bench": c.bench,
                                "canonical": c.canonical,
                                "parseable": c.parseable,
                                "parent_case_type": c.parent_case_type,
                                "parent_case_number": c.parent_case_number,
                                "parent_year": c.parent_year,
                                "parent_bench": c.parent_bench,
                            }
                            for c in it.normalized_cases
                        ],
                        "parties": it.parties,
                        "purpose": it.purpose,
                        "section": it.section,
                        "remarks": it.remarks,
                        "raw_text": it.raw_text,
                    }
                    for it in parsed.items
                ],
                "unparsed_lines": parsed.unparsed_lines_count,
                "layout_drift": parsed.layout_drift,
                "drift_reason": parsed.drift_reason,
                "total_pages": parsed.total_pages,
            }

            publish_event(
                event_type="court.causelist.published.v1",
                source=f"p0/{self.adapter_id}@{self.version}",
                subject=f"NCLT/{bench_code}/{court_no}/{list_date_str}",
                dataschema="schemareg://plc/court.causelist.published.v1/1.0",
                dataclass="PUBLIC",
                tenantid=None,
                idempotencykey=f"causelist|NCLT|{bench_code}|{court_no}|{list_date_str}|{raw_id}",
                schemaversion="1.0",
                data=causelist_event_data,
                topic="plc.court.causelist.published.v1",
                partition_key=f"NCLT|{bench_code}|{court_no}",
                lane="rt",
                now=now,
            )

        return parsed
