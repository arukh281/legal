"""Tests for cross-process per-host rate limiting in PostgreSQL.

Normative source:
- Session S04 Directive #2: Rate limit must hold across processes.
  Enforce per-host minimum delay through Postgres (advisory lock + last_request_at).
  Test with 2 concurrent workers.
- Session S04 Final Closure: Spacing must never be below profile value.
"""

from __future__ import annotations

import concurrent.futures
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from django.db import connection

from anchor_lib.ids import mint_id
from core.http_client import RawHttpResponse
from ingest.gate import GatedHttpClient, enforce_host_rate_limit
from ingest.models import HostRateLimit, LegalProfile, Source


@pytest.mark.django_db(transaction=True)
def test_concurrent_host_rate_limiting() -> None:
    """Verify 2 concurrent workers hitting the same host are serialized and delayed (Directive #2)."""
    host = "test.rate-limit.ibbi.gov.in"
    min_delay = 0.5  # 500 ms delay for test speed

    completion_times: list[float] = []

    def worker_job(worker_id: int) -> float:
        # Each thread gets its own DB connection
        connection.connect()
        try:
            enforce_host_rate_limit(host=host, min_delay_seconds=min_delay)
            finish_time = time.monotonic()
            return finish_time
        finally:
            connection.close()

    # Launch 2 workers concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(worker_job, 1)
        f2 = executor.submit(worker_job, 2)
        t1 = f1.result()
        t2 = f2.result()

    completion_times = sorted([t1, t2])
    gap = completion_times[1] - completion_times[0]

    # The gap between completions must strictly be at or above min_delay floor
    assert gap >= min_delay, f"Expected gap >= {min_delay}s, got {gap:.4f}s between workers."

    # Verify DB record
    record = HostRateLimit.objects.filter(host=host).first()
    assert record is not None
    assert record.min_delay_seconds == min_delay


@pytest.mark.django_db(transaction=True)
def test_spacing_is_never_below_profile_value() -> None:
    """Assert that request spacing is NEVER below the legal profile floor."""
    host = "test-floor.ibbi.gov.in"
    profile_delay = 0.15  # 150ms delay for fast test execution

    # 1. Test database-level enforce_host_rate_limit floor across repeated requests
    timestamps: list[float] = []
    for _ in range(4):
        enforce_host_rate_limit(host=host, min_delay_seconds=profile_delay)
        timestamps.append(time.monotonic())

    intervals = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]
    for idx, interval in enumerate(intervals):
        assert interval >= profile_delay, (
            f"DB rate limiter interval #{idx + 1} ({interval:.4f}s) was below floor ({profile_delay}s)"
        )

    # 2. Test GatedHttpClient observed_intervals guarantee
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

    LegalProfile.objects.filter(source_id="IBBI_ORDERS").update(status="SUSPENDED")
    LegalProfile.objects.create(
        profile_id=mint_id("lp"),
        source=source,
        status="PROVISIONAL",
        permitted_access_modes=["OPEN"],
        rate_limit_delay_seconds=profile_delay,
        allowed_hours_start_ist=0,
        allowed_hours_end_ist=24,
        backfill_allowed_start_ist=23,
        backfill_allowed_end_ist=7,
        backfill_night_only=False,
        terms_ref="tou_ibbi@2026-10-01",
        expires_at=datetime.now(UTC) + timedelta(days=90),
    )

    client = GatedHttpClient(source_id="IBBI_ORDERS")
    mock_raw = MagicMock()
    mock_raw.get.return_value = RawHttpResponse(
        status_code=200,
        headers={"content-type": "text/html"},
        content=b"<html>OK</html>",
        url="https://ibbi.gov.in/orders/nclt",
    )
    client._raw_client = mock_raw

    # Dispatch 4 sequential requests
    for page in range(1, 5):
        client.get(f"https://ibbi.gov.in/orders/nclt?page={page}")

    assert len(client.observed_intervals) == 3
    for idx, interval in enumerate(client.observed_intervals):
        assert interval >= profile_delay, (
            f"Observed interval #{idx + 1} ({interval:.4f}s) was below profile floor ({profile_delay}s)"
        )
