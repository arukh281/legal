"""Tests for cross-process per-host rate limiting in PostgreSQL.

Normative source:
- Session S04 Directive #2: Rate limit must hold across processes.
  Enforce per-host minimum delay through Postgres (advisory lock + last_request_at).
  Test with 2 concurrent workers.
"""

from __future__ import annotations

import concurrent.futures
import time

import pytest
from django.db import connection

from ingest.gate import enforce_host_rate_limit
from ingest.models import HostRateLimit


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

    # The gap between completions must be at least min_delay (with small tolerance for OS scheduling)
    assert gap >= 0.40, f"Expected gap >= 0.40s, got {gap:.3f}s between workers."

    # Verify DB record
    record = HostRateLimit.objects.filter(host=host).first()
    assert record is not None
    assert record.min_delay_seconds == min_delay
