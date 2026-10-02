"""Tests for crawler crash recovery and resumption via CrawlCheckpoint.

Normative sources:
- docs/02_P0_source_acquisition.md §5.8 (resilience and resumability)
- docs/mvp/03_data_model_and_contracts.md §3.2 (plc.crawl_checkpoint)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from anchor_lib.ids import mint_id
from core.http_client import RawHttpResponse
from ingest.adapters.ibbi import IBBIAdapter
from ingest.crawler import SourceCrawler
from ingest.models import Capture, CrawlCheckpoint, LegalProfile, RawBlob, Source
from ingest.storage import BlobStorage

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "eval" / "fixtures" / "ibbi"


@pytest.fixture
def seeded_ibbi_source(db: None) -> Source:
    source, _ = Source.objects.get_or_create(
        source_id="IBBI_ORDERS",
        defaults={
            "name": "IBBI Orders Mirror",
            "base_url": "https://ibbi.gov.in",
            "provenance_tier": "OFFICIAL_AGGREGATOR",
            "default_rights_class": "OFFICIAL",
            "terms_ref": "tou_ibbi@2026-10-01",
            "hotness": "WARM",
            "enabled": True,
        },
    )

    blob, _ = RawBlob.objects.get_or_create(
        raw_id="sha256:1111111111111111111111111111111111111111111111111111111111111111",
        defaults={
            "storage_uri": "s3://plc-raw/tou.html",
            "byte_size": 100,
            "content_type": "text/html",
            "first_seen_at": datetime.now(UTC),
        },
    )

    LegalProfile.objects.update_or_create(
        source=source,
        defaults={
            "profile_id": mint_id("lp"),
            "status": "PROVISIONAL",
            "permitted_access_modes": ["OPEN"],
            "rate_limit_delay_seconds": 0.0,
            "allowed_hours_start_ist": 0,
            "allowed_hours_end_ist": 24,
            "backfill_allowed_start_ist": 23,
            "backfill_allowed_end_ist": 7,
            "backfill_night_only": False,
            "tou_raw": blob,
            "terms_ref": "tou_ibbi@2026-10-01",
            "expires_at": datetime.now(UTC) + timedelta(days=90),
        },
    )

    return source


class InMemoryBlobStorage(BlobStorage):
    """In-memory mock storage avoiding real S3 calls during offline unit tests."""

    def __init__(self) -> None:
        super().__init__()
        self.blobs: dict[str, bytes] = {}

    def store_blob(
        self,
        data: bytes,
        *,
        content_type: str = "application/pdf",
        first_seen_at: datetime | None = None,
    ) -> tuple[str, str, int]:
        raw_id = self.compute_raw_id(data)
        byte_size = len(data)
        first_seen = first_seen_at or datetime.now(UTC)
        storage_uri = f"s3://plc-raw/test/{raw_id}.pdf"

        existing = RawBlob.objects.filter(raw_id=raw_id).first()
        if existing is not None:
            return existing.raw_id, existing.storage_uri, existing.byte_size

        self.blobs[raw_id] = data
        RawBlob.objects.create(
            raw_id=raw_id,
            storage_uri=storage_uri,
            byte_size=byte_size,
            content_type=content_type,
            first_seen_at=first_seen,
        )
        return raw_id, storage_uri, byte_size


def make_multipage_offline_resolver() -> tuple[Any, dict[str, int]]:
    """Resolver serving real page 1 and page 2 HTML plus sample PDFs."""
    stats = {"pages_requested": 0, "pdf_downloads": 0}
    page1_html = (FIXTURES_DIR / "nclt_page1.html").read_text(encoding="utf-8")
    page2_html = (FIXTURES_DIR / "nclt_page2.html").read_text(encoding="utf-8")
    sample_pdf = (FIXTURES_DIR / "sample_order_1.pdf").read_bytes()

    def resolver(url: str) -> RawHttpResponse | None:
        if "page=2" in url:
            stats["pages_requested"] += 1
            return RawHttpResponse(
                status_code=200,
                headers={"content-type": "text/html"},
                content=page2_html.encode("utf-8"),
                url=url,
            )
        elif "/orders/nclt" in url:
            stats["pages_requested"] += 1
            return RawHttpResponse(
                status_code=200,
                headers={"content-type": "text/html"},
                content=page1_html.encode("utf-8"),
                url=url,
            )
        elif url.endswith(".pdf"):
            stats["pdf_downloads"] += 1
            return RawHttpResponse(
                status_code=200,
                headers={"content-type": "application/pdf"},
                content=sample_pdf,
                url=url,
            )
        return None

    return resolver, stats


@pytest.mark.django_db
def test_interrupted_crawl_resumes_from_checkpoint(seeded_ibbi_source: Source) -> None:
    """A crawl interrupted after page 1 resumes with the same crawl_run_id and does not duplicate page 1."""
    storage = InMemoryBlobStorage()
    resolver, stats = make_multipage_offline_resolver()
    adapter = IBBIAdapter()

    crawler = SourceCrawler(
        adapter=adapter,
        storage=storage,
        offline_fixture_resolver=resolver,
    )

    fixed_run_id = mint_id("crun")

    # Step 1: Run crawl with max_pages=1 (simulating crash / shutdown after page 1)
    summary1 = crawler.crawl_section(
        "nclt",
        mode="backfill",
        max_pages=1,
        crawl_run_id=fixed_run_id,
    )

    assert summary1.status == "SUCCESS"
    assert summary1.pages_crawled == 1
    assert summary1.items_total == 20
    assert summary1.new_count == 20

    # Verify page 1 checkpoint exists
    p1_checkpoint = CrawlCheckpoint.objects.filter(
        crawl_run_id=fixed_run_id, section="nclt", page_number=1
    ).first()
    assert p1_checkpoint is not None
    assert p1_checkpoint.items_count == 20

    initial_captures_count = Capture.objects.count()
    assert initial_captures_count == 20

    # Step 2: Resume crawl with the SAME crawl_run_id, now up to max_pages=2
    stats["pages_requested"] = 0
    stats["pdf_downloads"] = 0

    summary2 = crawler.crawl_section(
        "nclt",
        mode="backfill",
        max_pages=2,
        crawl_run_id=fixed_run_id,
    )

    assert summary2.status == "SUCCESS"
    # Page 1 was skipped via checkpoint; only page 2 was crawled
    assert summary2.pages_crawled == 1
    assert summary2.items_total == 20
    # IBBI pagination can have 1-2 overlapping items across consecutive pages
    assert summary2.new_count + summary2.unchanged_count == 20
    assert summary2.unchanged_count >= 1

    # Total captures now 40 (20 from run 1 + 20 from run 2)
    assert Capture.objects.count() == 40

    # Verify both checkpoints exist
    checkpoints = CrawlCheckpoint.objects.filter(
        crawl_run_id=fixed_run_id, section="nclt"
    ).order_by("page_number")
    assert checkpoints.count() == 2
    assert [c.page_number for c in checkpoints] == [1, 2]
