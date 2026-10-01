"""Field-for-field verification of outbox events emitted during capture.

Normative sources:
- docs/01_master_architecture.md §6.3 (raw.captured.v1), §6.4 (source.health.v1)
- docs/mvp/03_data_model_and_contracts.md §4 (outbox contracts)
- Session S04 Directive #8: Exact topic names, lane in lane column, null fields present.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from anchor_lib.ids import mint_id
from core.http_client import RawHttpResponse
from ingest.adapters.ibbi import IBBIAdapter
from ingest.crawler import SourceCrawler
from ingest.models import LegalProfile, RawBlob, Source
from ingest.storage import BlobStorage
from ops.models import EventOutbox

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "eval" / "fixtures" / "ibbi"


@pytest.fixture
def seeded_ibbi_source(db: None) -> tuple[Source, LegalProfile]:
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

    profile, _ = LegalProfile.objects.update_or_create(
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

    return source, profile


class InMemoryBlobStorage(BlobStorage):
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
def test_raw_captured_v1_payload_matches_schema(
    seeded_ibbi_source: tuple[Source, LegalProfile],
) -> None:
    """Validate every field in raw.captured.v1 against master architecture §6.3 and Directive #8."""
    source, profile = seeded_ibbi_source
    storage = InMemoryBlobStorage()

    page1_html = (FIXTURES_DIR / "nclt_page1.html").read_text(encoding="utf-8")
    sample_pdf = (FIXTURES_DIR / "sample_order_1.pdf").read_bytes()

    def resolver(url: str) -> RawHttpResponse:
        if url.endswith(".pdf"):
            return RawHttpResponse(200, {"content-type": "application/pdf"}, sample_pdf, url)
        return RawHttpResponse(200, {"content-type": "text/html"}, page1_html.encode("utf-8"), url)

    adapter = IBBIAdapter()
    crawler = SourceCrawler(adapter=adapter, storage=storage, offline_fixture_resolver=resolver)

    fixed_run_id = mint_id("crun")
    crawler.crawl_section("nclt", mode="delta", max_pages=1, crawl_run_id=fixed_run_id)

    # 1. Fetch emitted raw.captured.v1 outbox events
    events = list(EventOutbox.objects.filter(type="raw.captured.v1").order_by("created_at"))
    assert len(events) == 20

    event = events[0]

    # CloudEvents envelope checks
    assert event.specversion == "1.0"
    assert event.type == "raw.captured.v1"
    assert event.source == f"p0/{adapter.adapter_id}@{adapter.version}"
    assert event.topic == "plc.raw.captured.v1"  # Directive #8: exact topic
    assert event.lane == "rt"  # Directive #8: lane column has rt
    assert event.dataclass == "PUBLIC"
    assert event.tenantid is None
    assert event.dataschema == "schemareg://plc/raw.captured.v1/1.0"

    # Data payload field-for-field verification against §6.3
    data = event.data
    assert data["raw_id"].startswith("sha256:")
    assert len(data["raw_id"]) == 71  # sha256: + 64 hex chars
    assert data["capture_id"].startswith("cap_")
    assert data["source_id"] == "IBBI_ORDERS"
    assert data["source_record_key"].startswith("nclt:")
    assert data["url"].startswith("https://ibbi.gov.in/uploads/order/")
    assert "fetched_at" in data
    assert "first_seen_at" in data
    assert data["storage_uri"].startswith("s3://")
    assert isinstance(data["byte_size"], int) and data["byte_size"] > 0
    assert data["http"] == {"status": 200, "content_type": "application/pdf"}
    assert isinstance(data["source_metadata"], dict)
    assert data["change_kind"] == "NEW"
    assert data["prior_raw_id"] is None
    assert data["crawl_run_id"] == fixed_run_id
    assert data["terms_ref"] == "tou_ibbi@2026-10-01"

    # Directive #8: Fields MVP doesn't produce are present and null
    assert data["warc"] is None
    assert data["norm_fingerprint"] is None
    assert data["near_dup_hint"] is None

    # Fetch context check (Directive #4)
    fc = data["fetch_context"]
    assert fc["adapter"] == f"{adapter.adapter_id}@{adapter.version}"
    assert fc["access_mode"] == "OPEN"
    assert fc["egress_region"] == "IN"
    assert fc["browser"] is False
    assert fc["priority"] == "P2"
    assert fc["pdf_fetched"] is True
    assert fc["profile_id"] == profile.profile_id

    # Provenance and rights class (D9/D16)
    assert data["provenance_tier"] == "OFFICIAL_AGGREGATOR"
    assert data["rights_class"] == "OFFICIAL"

    # Flags
    flags = data["flags"]
    assert flags["text_layer"] == "unknown"
    assert flags["malware_suspect"] is False
    assert flags["injection_suspect"] is False
    assert flags["soft_error_suspect"] is False
    assert flags["suspected_replacement"] is False
    assert flags["key_quality"] == "STRONG"
    assert flags["uncertified"] is True


@pytest.mark.django_db
def test_source_health_v1_payload_matches_schema(
    seeded_ibbi_source: tuple[Source, LegalProfile],
) -> None:
    """Validate every field in source.health.v1 against master architecture §6.4 and Directive #8."""
    storage = InMemoryBlobStorage()
    page1_html = (FIXTURES_DIR / "nclt_page1.html").read_text(encoding="utf-8")
    sample_pdf = (FIXTURES_DIR / "sample_order_1.pdf").read_bytes()

    def resolver(url: str) -> RawHttpResponse:
        if url.endswith(".pdf"):
            return RawHttpResponse(200, {"content-type": "application/pdf"}, sample_pdf, url)
        return RawHttpResponse(200, {"content-type": "text/html"}, page1_html.encode("utf-8"), url)

    adapter = IBBIAdapter()
    crawler = SourceCrawler(adapter=adapter, storage=storage, offline_fixture_resolver=resolver)

    crawler.crawl_section("nclt", mode="delta", max_pages=1)

    health_events = list(EventOutbox.objects.filter(type="source.health.v1"))
    assert len(health_events) >= 1

    event = health_events[0]
    assert event.type == "source.health.v1"
    assert event.topic == "plc.source.health.v1"  # Directive #8
    assert event.lane == "rt"
    assert event.dataclass == "PUBLIC"
    assert event.tenantid is None
    assert event.dataschema == "schemareg://plc/source.health.v1/1.0"

    data = event.data
    assert data["source_id"] == "IBBI_ORDERS"
    assert data["status"] == "OK"
    assert data["freshness_lag_p95_min"] == 60
    assert data["last_success_at"] is not None
    assert data["coverage_estimate"] == 1.0
    assert data["expected_pending"] == 0
    assert data["backing"] == "LIVE_DELTA"
    assert data["incident_id"] is None
