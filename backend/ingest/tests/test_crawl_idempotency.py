"""Tests for crawl idempotency and change detection.

Normative sources:
- Session S04 Directive #7: Don't re-download every PDF on every delta run.
- docs/02_P0_source_acquisition.md §5.6 (change detection)
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
from ingest.models import Capture, LegalProfile, RawBlob, Source
from ingest.storage import BlobStorage
from ops.models import EventOutbox

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
            "rate_limit_delay_seconds": 0.0,  # Fast for tests
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


def make_offline_resolver(
    pdf_override: bytes | None = None,
) -> tuple[Any, dict[str, int]]:
    """Create an offline fixture resolver that counts PDF fetches."""
    stats = {"pdf_downloads": 0, "listing_downloads": 0}

    page1_html = (FIXTURES_DIR / "nclt_page1.html").read_text(encoding="utf-8")
    sample_pdf_bytes = (FIXTURES_DIR / "sample_order_1.pdf").read_bytes()

    def resolver(url: str) -> RawHttpResponse | None:
        if "page=" in url or "/orders/nclt" in url:
            stats["listing_downloads"] += 1
            return RawHttpResponse(
                status_code=200,
                headers={"content-type": "text/html"},
                content=page1_html.encode("utf-8"),
                url=url,
            )
        elif url.endswith(".pdf"):
            stats["pdf_downloads"] += 1
            content = pdf_override if pdf_override is not None else sample_pdf_bytes
            return RawHttpResponse(
                status_code=200,
                headers={"content-type": "application/pdf"},
                content=content,
                url=url,
            )
        return None

    return resolver, stats


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


@pytest.mark.django_db
def test_crawl_idempotency_and_no_redownload(seeded_ibbi_source: Source) -> None:
    """Verify first crawl yields NEW, second crawl yields UNCHANGED with ZERO duplicate downloads (Directive #7)."""
    storage = InMemoryBlobStorage()
    resolver, stats = make_offline_resolver()

    adapter = IBBIAdapter()
    crawler = SourceCrawler(
        adapter=adapter,
        storage=storage,
        offline_fixture_resolver=resolver,
    )

    # 1. Run 1: initial crawl of page 1
    summary1 = crawler.crawl_section("nclt", mode="delta", max_pages=1)

    assert summary1.status == "SUCCESS"
    assert summary1.pages_crawled == 1
    assert summary1.items_total == 20
    assert summary1.new_count == 20
    assert summary1.unchanged_count == 0
    assert stats["pdf_downloads"] == 20
    initial_blobs_count = RawBlob.objects.count()
    assert initial_blobs_count >= 1

    # Verify outbox events emitted
    outbox_events = EventOutbox.objects.filter(type="raw.captured.v1")
    assert outbox_events.count() == 20

    first_capture = Capture.objects.filter(change_kind="NEW").first()
    assert first_capture is not None
    assert first_capture.rights_class == "OFFICIAL"
    assert first_capture.provenance_tier == "OFFICIAL_AGGREGATOR"
    assert first_capture.fetch_context is not None
    assert first_capture.fetch_context["pdf_fetched"] is True

    # 2. Run 2: delta re-crawl of the same page
    stats["pdf_downloads"] = 0
    summary2 = crawler.crawl_section("nclt", mode="delta", max_pages=1)

    assert summary2.status == "SUCCESS"
    assert summary2.items_total == 20
    assert summary2.unchanged_count == 20
    assert summary2.new_count == 0
    # ZERO PDF downloads on unchanged delta run! (Directive #7)
    assert stats["pdf_downloads"] == 0
    # Zero new raw blobs created
    assert RawBlob.objects.count() == initial_blobs_count

    unchanged_capture = Capture.objects.filter(change_kind="UNCHANGED").first()
    assert unchanged_capture is not None
    assert unchanged_capture.fetch_context is not None
    assert unchanged_capture.fetch_context["pdf_fetched"] is False


@pytest.mark.django_db
def test_changed_pdf_records_changed_and_prior_raw_id(seeded_ibbi_source: Source) -> None:
    """Verify a modified PDF produces CHANGED with prior_raw_id pointing to previous blob."""
    storage = InMemoryBlobStorage()
    adapter = IBBIAdapter()

    # Initial crawl with standard PDF
    resolver1, _ = make_offline_resolver()
    crawler1 = SourceCrawler(adapter=adapter, storage=storage, offline_fixture_resolver=resolver1)
    crawler1.crawl_section("nclt", mode="delta", max_pages=1)

    initial_capture = Capture.objects.filter(
        source_record_key="nclt:2026-09-29-115640-houbm-a240fa27925a635b08dc28c9e4f9216d"
    ).first()
    assert initial_capture is not None
    old_raw_id = initial_capture.raw_id

    # Second crawl with modified PDF bytes (simulating amended/re-uploaded order)
    changed_pdf_bytes = (FIXTURES_DIR / "sample_order_changed.pdf").read_bytes()
    resolver2, _ = make_offline_resolver(pdf_override=changed_pdf_bytes)

    # Note: to trigger re-download, the URL changes or file content changes
    # When file content changed:
    crawler2 = SourceCrawler(adapter=adapter, storage=storage, offline_fixture_resolver=resolver2)

    # Let's test _process_listing_item directly with a changed PDF download:
    item = adapter.parse_listing_page((FIXTURES_DIR / "nclt_page1.html").read_text(), "nclt", 1)[0]
    # Simulate IBBI publishing a replacement file URL for this item
    item = item.__class__(
        record_key=item.record_key,
        detail_url=item.detail_url,
        file_url="https://ibbi.gov.in/uploads/order/2026-09-29-replacement.pdf",
        source_metadata=dict(
            item.source_metadata,
            pdf_url="https://ibbi.gov.in/uploads/order/2026-09-29-replacement.pdf",
        ),
        page_number=1,
        row_index=0,
    )

    client = crawler2._get_client(crawl_mode="delta")
    outcome = crawler2._process_listing_item(
        item=item,
        crawl_run_id=mint_id("crun"),
        crawl_mode="delta",
        client=client,
    )

    assert outcome == "CHANGED"

    latest_capture = (
        Capture.objects.filter(source_record_key=item.record_key).order_by("-fetched_at").first()
    )
    assert latest_capture is not None
    assert latest_capture.change_kind == "CHANGED"
    assert latest_capture.prior_raw_id == old_raw_id
    assert latest_capture.raw_id != old_raw_id
    assert latest_capture.fetch_context is not None
    assert latest_capture.fetch_context["pdf_fetched"] is True
