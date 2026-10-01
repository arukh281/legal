"""Tests for crawler safety breakers: CAPTCHA, Layout Drift, Mass Change.

Normative sources:
- Non-negotiable #5: Never solve, bypass or automate a CAPTCHA.
- docs/02_P0_source_acquisition.md §5.8 (safety breakers: CAPTCHA, layout drift, mass-change)
- Session S04 Directive #9: Mass-change breaker halts run and marks source DEGRADED.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from anchor_lib.ids import mint_id
from core.http_client import RawHttpResponse
from ingest.adapters.base import ListingItem
from ingest.adapters.ibbi import IBBIAdapter
from ingest.crawler import SafetyBreakerTriggered, SourceCrawler
from ingest.models import LegalProfile, RawBlob, Source, SourceHealth
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


@pytest.mark.django_db
def test_captcha_breaker_halts_immediately_and_marks_blocked(seeded_ibbi_source: Source) -> None:
    """Non-negotiable #5: CAPTCHA page immediately halts the crawl and marks source BLOCKED."""
    storage = InMemoryBlobStorage()
    captcha_html = (FIXTURES_DIR / "captcha_page.html").read_text(encoding="utf-8")

    def resolver(url: str) -> RawHttpResponse:
        return RawHttpResponse(
            status_code=200,
            headers={"content-type": "text/html"},
            content=captcha_html.encode("utf-8"),
            url=url,
        )

    adapter = IBBIAdapter()
    crawler = SourceCrawler(adapter=adapter, storage=storage, offline_fixture_resolver=resolver)

    run_id = mint_id("crun")
    with pytest.raises(SafetyBreakerTriggered) as exc_info:
        crawler.crawl_section("nclt", crawl_run_id=run_id)

    assert exc_info.value.breaker_type == "CAPTCHA_DETECTED"
    assert "CAPTCHA detected" in str(exc_info.value)

    # Health check recorded as BLOCKED
    latest_health = (
        SourceHealth.objects.filter(source_id="IBBI_ORDERS").order_by("-observed_at").first()
    )
    assert latest_health is not None
    assert latest_health.status == "BLOCKED"
    assert latest_health.incident_id == f"CAPTCHA_{run_id}"


@pytest.mark.django_db
def test_layout_drift_breaker_halts_and_marks_degraded(seeded_ibbi_source: Source) -> None:
    """Layout drift breaker: Corrupted table or 0 items in listing marks source DEGRADED."""
    storage = InMemoryBlobStorage()
    corrupt_html = (FIXTURES_DIR / "corrupt_listing.html").read_text(encoding="utf-8")

    def resolver(url: str) -> RawHttpResponse:
        return RawHttpResponse(
            status_code=200,
            headers={"content-type": "text/html"},
            content=corrupt_html.encode("utf-8"),
            url=url,
        )

    adapter = IBBIAdapter()
    crawler = SourceCrawler(adapter=adapter, storage=storage, offline_fixture_resolver=resolver)

    run_id = mint_id("crun")
    with pytest.raises(SafetyBreakerTriggered) as exc_info:
        crawler.crawl_section("nclt", crawl_run_id=run_id)

    assert exc_info.value.breaker_type == "LAYOUT_DRIFT"
    assert "Layout drift detected" in str(exc_info.value)

    # Health check recorded as DEGRADED
    latest_health = (
        SourceHealth.objects.filter(source_id="IBBI_ORDERS").order_by("-observed_at").first()
    )
    assert latest_health is not None
    assert latest_health.status == "DEGRADED"
    assert latest_health.incident_id == f"LAYOUT_DRIFT_{run_id}"


@pytest.mark.django_db
def test_mass_change_breaker_halts_and_marks_degraded(seeded_ibbi_source: Source) -> None:
    """Directive #9: If >10% of items change (after >=20 items), halt crawl and mark DEGRADED."""
    storage = InMemoryBlobStorage()
    adapter = IBBIAdapter()

    # Initial crawl of page 1 with normal order PDF
    page1_html = (FIXTURES_DIR / "nclt_page1.html").read_text(encoding="utf-8")
    sample_pdf = (FIXTURES_DIR / "sample_order_1.pdf").read_bytes()

    def resolver(url: str) -> RawHttpResponse:
        if url.endswith(".pdf"):
            return RawHttpResponse(200, {"content-type": "application/pdf"}, sample_pdf, url)
        return RawHttpResponse(200, {"content-type": "text/html"}, page1_html.encode("utf-8"), url)

    crawler1 = SourceCrawler(adapter=adapter, storage=storage, offline_fixture_resolver=resolver)
    crawler1.crawl_section("nclt", max_pages=1)

    # Second crawl: mock adapter to return items where 3 out of 20 (>10%) have changed PDF URLs
    changed_pdf = (FIXTURES_DIR / "sample_order_changed.pdf").read_bytes()

    def resolver2(url: str) -> RawHttpResponse:
        if "changed" in url:
            return RawHttpResponse(200, {"content-type": "application/pdf"}, changed_pdf, url)
        elif url.endswith(".pdf"):
            return RawHttpResponse(200, {"content-type": "application/pdf"}, sample_pdf, url)
        return RawHttpResponse(200, {"content-type": "text/html"}, page1_html.encode("utf-8"), url)

    class MutatedAdapter(IBBIAdapter):
        def parse_listing_page(
            self, html: str, section: str, page_number: int
        ) -> list[ListingItem]:
            base_items = super().parse_listing_page(html, section, page_number)
            # Modify 3 items (indices 0, 1, 2) out of 20 (15% > 10%) with replacement PDF URLs
            mutated = []
            for i, it in enumerate(base_items):
                if i < 3:
                    new_file_url = f"https://ibbi.gov.in/uploads/order/changed_{i}.pdf"
                    new_meta = dict(it.source_metadata, pdf_url=new_file_url)
                    mutated.append(
                        ListingItem(
                            record_key=it.record_key,
                            detail_url=it.detail_url,
                            file_url=new_file_url,
                            source_metadata=new_meta,
                            page_number=it.page_number,
                            row_index=it.row_index,
                        )
                    )
                else:
                    mutated.append(it)
            return mutated

    crawler2 = SourceCrawler(
        adapter=MutatedAdapter(),
        storage=storage,
        offline_fixture_resolver=resolver2,
    )

    run_id2 = mint_id("crun")
    with pytest.raises(SafetyBreakerTriggered) as exc_info:
        crawler2.crawl_section("nclt", mode="delta", max_pages=1, crawl_run_id=run_id2)

    assert exc_info.value.breaker_type == "MASS_CHANGE"
    assert "Changed fraction exceeded 10%" in str(exc_info.value)

    # Health check recorded as DEGRADED
    latest_health = (
        SourceHealth.objects.filter(source_id="IBBI_ORDERS").order_by("-observed_at").first()
    )
    assert latest_health is not None
    assert latest_health.status == "DEGRADED"
    assert latest_health.incident_id == f"MASS_CHANGE_{run_id2}"
