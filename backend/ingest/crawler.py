"""Resumable source crawler engine for legal listing sources.

Normative sources:
- docs/mvp/01_corporate_corpus_and_sources.md §6.2
- docs/02_P0_source_acquisition.md §5.5, §5.6, §5.8, §5.12
- docs/mvp/03_data_model_and_contracts.md §3.2, §4
- docs/01_master_architecture.md §6.3 (raw.captured.v1), §6.4 (source.health.v1)
- Session S04 Directives #1–#9
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import structlog
from django.db import transaction

from anchor_lib.ids import mint_id
from ingest.adapters.base import BaseListingAdapter, ListingItem
from ingest.gate import GatedHttpClient
from ingest.models import Capture, CrawlCheckpoint, LegalProfile, SourceHealth
from ingest.storage import BlobStorage
from ops.outbox import publish_event

logger = structlog.get_logger(__name__)


class SafetyBreakerTriggered(Exception):
    """Raised when a safety breaker (CAPTCHA, Layout Drift, Mass Change) halts the crawl."""

    def __init__(self, breaker_type: str, message: str) -> None:
        super().__init__(f"{breaker_type}: {message}")
        self.breaker_type = breaker_type


@dataclass
class CrawlSummary:
    """Summary metrics of a crawl run."""

    crawl_run_id: str
    source_id: str
    section: str
    mode: str
    pages_crawled: int
    items_total: int
    new_count: int
    unchanged_count: int
    changed_count: int
    metadata_changed_count: int
    status: str
    error: str | None = None


class SourceCrawler:
    """Resumable, auditable source crawler for listing-based legal authorities."""

    def __init__(
        self,
        adapter: BaseListingAdapter,
        *,
        storage: BlobStorage | None = None,
        gated_client: GatedHttpClient | None = None,
        offline_fixture_resolver: Callable[[str], Any] | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self.adapter = adapter
        self.storage = storage or BlobStorage()
        self.offline_fixture_resolver = offline_fixture_resolver
        self.now_fn = now_fn or (lambda: datetime.now(UTC))
        self._gated_client = gated_client

    def _get_client(self, crawl_mode: str) -> GatedHttpClient:
        if self._gated_client is not None:
            return self._gated_client
        return GatedHttpClient(
            source_id=self.adapter.source_id,
            access_mode="OPEN",
            crawl_mode=crawl_mode,
            offline_fixture_resolver=self.offline_fixture_resolver,
            now_fn=self.now_fn,
        )

    def crawl_section(
        self,
        section: str,
        *,
        mode: str = "delta",
        max_pages: int | None = None,
        crawl_run_id: str | None = None,
        stop_on_unchanged_count: int = 20,
    ) -> CrawlSummary:
        """Run a resumable crawl across a specific source section.

        In delta mode: terminates cleanly when stop_on_unchanged_count consecutive
        unchanged records are observed.
        In backfill mode: iterates through requested pages.
        Checkpoints after each page; safe to kill and restart with the same crawl_run_id.
        """
        run_id = crawl_run_id or mint_id("crun")
        client = self._get_client(crawl_mode=mode)

        summary = CrawlSummary(
            crawl_run_id=run_id,
            source_id=self.adapter.source_id,
            section=section,
            mode=mode,
            pages_crawled=0,
            items_total=0,
            new_count=0,
            unchanged_count=0,
            changed_count=0,
            metadata_changed_count=0,
            status="RUNNING",
        )

        page_num = 1
        consecutive_unchanged = 0
        total_items_seen = 0
        changed_items_seen = 0

        logger.info(
            "crawl_run_started",
            crawl_run_id=run_id,
            source_id=self.adapter.source_id,
            section=section,
            mode=mode,
        )

        try:
            while True:
                if max_pages is not None and page_num > max_pages:
                    logger.info("crawl_max_pages_reached", max_pages=max_pages, page=page_num)
                    break

                # 1. Checkpoint inspection: skip page if already completed in this crawl run
                if CrawlCheckpoint.objects.filter(
                    crawl_run_id=run_id, section=section, page_number=page_num
                ).exists():
                    logger.info("skipping_checkpointed_page", page=page_num, crawl_run_id=run_id)
                    page_num += 1
                    continue

                page_url = self.adapter.build_page_url(section, page_num)
                page_resp = client.get(page_url)

                if page_resp.status_code != 200:
                    logger.warn("listing_page_non_200", url=page_url, status=page_resp.status_code)
                    break

                html_text = page_resp.text

                # 2. CAPTCHA Breaker: immediate halt, never solve or bypass
                if self.adapter.detect_captcha(html_text):
                    self._record_health(
                        status="BLOCKED",
                        incident_id=f"CAPTCHA_{run_id}",
                    )
                    raise SafetyBreakerTriggered(
                        "CAPTCHA_DETECTED",
                        f"CAPTCHA detected on {page_url}. Crawl halted immediately.",
                    )

                # 3. Parse listing items
                items = self.adapter.parse_listing_page(html_text, section, page_num)

                # 4. Layout Drift Breaker: check for missing tables or 0 items
                if self.adapter.detect_layout_drift(html_text, items):
                    self._record_health(
                        status="DEGRADED",
                        incident_id=f"LAYOUT_DRIFT_{run_id}",
                    )
                    raise SafetyBreakerTriggered(
                        "LAYOUT_DRIFT",
                        f"Layout drift detected on {page_url}. Parser yielded 0 items.",
                    )

                if not items:
                    # Clean end of listing
                    break

                # 5. Process each listing item
                for item in items:
                    total_items_seen += 1
                    summary.items_total += 1

                    outcome = self._process_listing_item(
                        item=item,
                        crawl_run_id=run_id,
                        crawl_mode=mode,
                        client=client,
                    )

                    if outcome == "UNCHANGED":
                        summary.unchanged_count += 1
                        consecutive_unchanged += 1
                    elif outcome == "NEW":
                        summary.new_count += 1
                        consecutive_unchanged = 0
                    elif outcome == "CHANGED":
                        summary.changed_count += 1
                        changed_items_seen += 1
                        consecutive_unchanged = 0
                    elif outcome == "METADATA_CHANGED":
                        summary.metadata_changed_count += 1
                        consecutive_unchanged = 0

                    # 6. Mass-change breaker (Directive #9)
                    if total_items_seen >= 20 and (changed_items_seen / total_items_seen) > 0.10:
                        self._record_health(
                            status="DEGRADED",
                            incident_id=f"MASS_CHANGE_{run_id}",
                        )
                        raise SafetyBreakerTriggered(
                            "MASS_CHANGE",
                            f"Changed fraction exceeded 10% ({changed_items_seen}/{total_items_seen}).",
                        )

                    # Delta termination check
                    if mode == "delta" and consecutive_unchanged >= stop_on_unchanged_count:
                        logger.info(
                            "delta_unchanged_streak_reached",
                            streak=consecutive_unchanged,
                            limit=stop_on_unchanged_count,
                        )
                        break

                # Record page checkpoint
                with transaction.atomic():
                    CrawlCheckpoint.objects.create(
                        crawl_run_id=run_id,
                        source_id=self.adapter.source_id,
                        section=section,
                        page_number=page_num,
                        items_count=len(items),
                        unchanged_streak=consecutive_unchanged,
                    )

                summary.pages_crawled += 1

                if mode == "delta" and consecutive_unchanged >= stop_on_unchanged_count:
                    break

                page_num += 1

            # Normal successful run completion
            summary.status = "SUCCESS"
            self._record_health(status="OK", incident_id=None)

        except SafetyBreakerTriggered as sbe:
            summary.status = "HALTED"
            summary.error = str(sbe)
            logger.error("crawl_safety_breaker_halted", error=str(sbe))
            raise
        except Exception as exc:
            summary.status = "FAILED"
            summary.error = str(exc)
            self._record_health(status="DEGRADED", incident_id=f"ERROR_{run_id}")
            logger.error("crawl_run_failed", error=str(exc))
            raise

        logger.info(
            "crawl_run_finished",
            crawl_run_id=run_id,
            status=summary.status,
            pages=summary.pages_crawled,
            items=summary.items_total,
            new=summary.new_count,
            unchanged=summary.unchanged_count,
            changed=summary.changed_count,
        )

        return summary

    def _process_listing_item(
        self,
        *,
        item: ListingItem,
        crawl_run_id: str,
        crawl_mode: str,
        client: GatedHttpClient,
    ) -> str:
        """Process a single listing row with content-addressed storage and event emission.

        Enforces Directive #7: avoids re-downloading PDFs if URL and metadata are unchanged.
        Emits raw.captured.v1 in the same transaction as the capture row.
        """
        now = self.now_fn()
        source_id = self.adapter.source_id

        # 1. Inspect existing captures for (source_id, source_record_key)
        latest_capture = (
            Capture.objects.filter(source_id=source_id, source_record_key=item.record_key)
            .order_by("-fetched_at")
            .first()
        )

        pdf_fetched = False
        raw_id: str
        storage_uri: str
        byte_size: int
        prior_raw_id: str | None = None
        change_kind: str

        if latest_capture is not None:
            # Listing row already exists from a prior crawl
            prior_meta = latest_capture.source_metadata
            meta_identical = (
                prior_meta.get("order_date") == item.source_metadata.get("order_date")
                and prior_meta.get("subject") == item.source_metadata.get("subject")
                and prior_meta.get("remarks") == item.source_metadata.get("remarks")
                and prior_meta.get("pdf_url") == item.file_url
            )

            if meta_identical:
                # UNCHANGED: Do NOT re-download PDF (Directive #7)
                change_kind = "UNCHANGED"
                raw_id = latest_capture.raw_id
                storage_uri = latest_capture.raw.storage_uri
                byte_size = latest_capture.raw.byte_size
                prior_raw_id = latest_capture.raw_id
                pdf_fetched = False
            elif prior_meta.get("pdf_url") == item.file_url:
                # Metadata changed but PDF URL is identical
                change_kind = "METADATA_CHANGED"
                raw_id = latest_capture.raw_id
                storage_uri = latest_capture.raw.storage_uri
                byte_size = latest_capture.raw.byte_size
                prior_raw_id = latest_capture.raw_id
                pdf_fetched = False
            else:
                # PDF URL changed: must download new PDF
                pdf_resp = client.get(item.file_url)
                pdf_bytes = pdf_resp.content
                raw_id, storage_uri, byte_size = self.storage.store_blob(
                    pdf_bytes, first_seen_at=now
                )
                prior_raw_id = latest_capture.raw_id
                change_kind = "CHANGED" if raw_id != prior_raw_id else "METADATA_CHANGED"
                pdf_fetched = True
        else:
            # NEW: Download PDF
            pdf_resp = client.get(item.file_url)
            pdf_bytes = pdf_resp.content
            raw_id, storage_uri, byte_size = self.storage.store_blob(pdf_bytes, first_seen_at=now)
            change_kind = "NEW"
            prior_raw_id = None
            pdf_fetched = True

        capture_id = mint_id("cap")
        first_seen_at = latest_capture.fetched_at if latest_capture is not None else now

        profile = (
            LegalProfile.objects.filter(source_id=source_id).exclude(status="SUSPENDED").first()
        )
        profile_id = profile.profile_id if profile else None

        fetch_context = {
            "adapter": f"{self.adapter.adapter_id}@{self.adapter.version}",
            "access_mode": "OPEN",
            "egress_region": "IN",
            "browser": False,
            "priority": "P2",
            "pdf_fetched": pdf_fetched,
            "acquisition_request_id": None,
            "profile_id": profile_id,
        }

        flags = {
            "text_layer": "unknown",
            "malware_suspect": False,
            "injection_suspect": False,
            "soft_error_suspect": False,
            "suspected_replacement": False,
            "key_quality": "STRONG",
            "uncertified": True,
        }

        raw_captured_payload: dict[str, Any] = {
            "raw_id": raw_id,
            "capture_id": capture_id,
            "source_id": source_id,
            "source_record_key": item.record_key,
            "url": item.file_url,
            "fetched_at": now.isoformat(),
            "first_seen_at": first_seen_at.isoformat(),
            "storage_uri": storage_uri,
            "byte_size": byte_size,
            "http": {"status": 200, "content_type": "application/pdf"},
            "source_metadata": item.source_metadata,
            "change_kind": change_kind,
            "prior_raw_id": prior_raw_id,
            "crawl_run_id": crawl_run_id,
            "terms_ref": "tou_ibbi@2026-10-01",
            "norm_fingerprint": None,
            "warc": None,
            "fetch_context": fetch_context,
            "provenance_tier": "OFFICIAL_AGGREGATOR",
            "rights_class": "OFFICIAL",
            "near_dup_hint": None,
            "flags": flags,
        }

        lane = "bulk" if crawl_mode == "backfill" else "rt"

        # Atomic commit of capture row and transactional outbox event
        with transaction.atomic():
            Capture.objects.create(
                capture_id=capture_id,
                raw_id=raw_id,
                source_id=source_id,
                source_record_key=item.record_key,
                url=item.file_url,
                fetched_at=now,
                change_kind=change_kind,
                prior_raw_id=prior_raw_id,
                source_metadata=item.source_metadata,
                rights_class="OFFICIAL",
                provenance_tier="OFFICIAL_AGGREGATOR",
                fetch_context=fetch_context,
                flags=flags,
                crawl_run_id=crawl_run_id,
            )

            # Emit raw.captured.v1 via outbox (Directive #8)
            publish_event(
                event_type="raw.captured.v1",
                source=f"p0/{self.adapter.adapter_id}@{self.adapter.version}",
                subject=f"{source_id}/{item.record_key}",
                dataschema="schemareg://plc/raw.captured.v1/1.0",
                dataclass="PUBLIC",
                tenantid=None,
                idempotencykey=f"p0|capture|{source_id}|{item.record_key}|{raw_id}",
                schemaversion="1.0",
                data=raw_captured_payload,
                topic="plc.raw.captured.v1",
                partition_key=f"{source_id}|{item.record_key}",
                lane=lane,
                now=now,
            )

        return change_kind

    def _record_health(self, status: str, incident_id: str | None) -> None:
        """Record health state in plc.source_health and emit source.health.v1."""
        now = self.now_fn()
        source_id = self.adapter.source_id

        health_payload: dict[str, Any] = {
            "source_id": source_id,
            "status": status,
            "freshness_lag_p95_min": 60,
            "last_success_at": now.isoformat() if status == "OK" else None,
            "coverage_estimate": 1.0 if status == "OK" else 0.5,
            "expected_pending": 0,
            "backing": "LIVE_DELTA",
            "incident_id": incident_id,
        }

        with transaction.atomic():
            SourceHealth.objects.create(
                source_id=source_id,
                observed_at=now,
                status=status,
                freshness_lag_p95_min=60,
                last_success_at=now if status == "OK" else None,
                coverage_estimate=1.0 if status == "OK" else 0.5,
                expected_pending=0,
                incident_id=incident_id,
            )

            # Emit source.health.v1 via outbox (Directive #8)
            publish_event(
                event_type="source.health.v1",
                source=f"p0/{self.adapter.adapter_id}@{self.adapter.version}",
                subject=source_id,
                dataschema="schemareg://plc/source.health.v1/1.0",
                dataclass="PUBLIC",
                tenantid=None,
                idempotencykey=f"p0|health|{source_id}|{now.isoformat()}",
                schemaversion="1.0",
                data=health_payload,
                topic="plc.source.health.v1",
                partition_key=source_id,
                lane="rt",
                now=now,
            )
