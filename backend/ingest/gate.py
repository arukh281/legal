"""Legal Gate and Gated HTTP Client.

Normative sources:
- Session S04 Directive #1: All network requests must pass through GatedHttpClient.
- Session S04 Directive #2: Per-host rate limiting holds across processes via PostgreSQL.
- Session S04 Directive #3: Configurable User-Agent and verified contact email.
- Session S04 Directive #4: Legal profile validation, single active profile, midnight-wrap check.
- docs/mvp/01_corporate_corpus_and_sources.md §6.2
- docs/02_P0_source_acquisition.md §5.2
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import structlog
from django.conf import settings
from django.db import connection, transaction

from core.http_client import RawHttpClient, RawHttpResponse
from ingest.models import LegalProfile

logger = structlog.get_logger(__name__)

IST = ZoneInfo("Asia/Kolkata")


class LegalGateViolation(Exception):
    """Raised when a proposed network call violates legal governance rules."""

    pass


def is_within_hours(current_hour: int, start_hour: int, end_hour: int) -> bool:
    """Check if current_hour is within [start_hour, end_hour).

    Handles midnight wraps correctly (e.g. 23:00 to 07:00 IST).
    """
    if start_hour <= end_hour:
        return start_hour <= current_hour < end_hour
    # Midnight wrap: e.g. 23 to 7 means hour >= 23 OR hour < 7
    return current_hour >= start_hour or current_hour < end_hour


def check_legal_gate(
    source_id: str,
    access_mode: str = "OPEN",
    crawl_mode: str = "delta",
    now: datetime | None = None,
) -> LegalProfile:
    """Execute the single legal gate check required before any network call.

    Checks:
    1. Active legal profile exists for the source.
    2. Profile status is PROVISIONAL or APPROVED (never SUSPENDED).
    3. Kill switch is not active.
    4. Profile is not expired (expires_at <= 180 days).
    5. Access mode is in permitted_access_modes.
    6. Current IST time is within general allowed hours.
    7. For backfill mode, current IST time is within night IST window.
    """
    if now is None:
        now = datetime.now(UTC)

    # Active profile: at most one non-SUSPENDED profile per source (Directive #4)
    profile = LegalProfile.objects.filter(source_id=source_id).exclude(status="SUSPENDED").first()

    if profile is None:
        raise LegalGateViolation(
            f"NO_LEGAL_PROFILE: No active legal profile found for source '{source_id}'."
        )

    if profile.status not in ("PROVISIONAL", "APPROVED"):
        raise LegalGateViolation(
            f"PROFILE_STATUS_INVALID: Source '{source_id}' legal profile status is '{profile.status}'."
        )

    if profile.kill_switch:
        raise LegalGateViolation(
            f"KILL_SWITCH_ACTIVE: Kill switch is engaged for source '{source_id}': {profile.kill_reason}."
        )

    if now > profile.expires_at:
        raise LegalGateViolation(
            f"PROFILE_EXPIRED: Legal profile '{profile.profile_id}' expired at {profile.expires_at}."
        )

    permitted = (
        profile.permitted_access_modes if isinstance(profile.permitted_access_modes, list) else []
    )
    if access_mode not in permitted:
        raise LegalGateViolation(
            f"ACCESS_MODE_NOT_PERMITTED: Access mode '{access_mode}' is not in permitted modes {permitted}."
        )

    # Allowed hours checks (IST)
    ist_now = now.astimezone(IST)
    current_hour = ist_now.hour

    # Backfill mode check (Directive #4)
    if crawl_mode == "backfill" and profile.backfill_night_only:
        if not is_within_hours(
            current_hour,
            profile.backfill_allowed_start_ist,
            profile.backfill_allowed_end_ist,
        ):
            raise LegalGateViolation(
                f"OUTSIDE_ALLOWED_HOURS: Backfill for source '{source_id}' is restricted to "
                f"night IST ({profile.backfill_allowed_start_ist}:00–{profile.backfill_allowed_end_ist}:00). "
                f"Current IST hour is {current_hour}:00."
            )

    # General allowed hours check
    if not is_within_hours(
        current_hour, profile.allowed_hours_start_ist, profile.allowed_hours_end_ist
    ):
        raise LegalGateViolation(
            f"OUTSIDE_ALLOWED_HOURS: Source '{source_id}' is restricted to "
            f"{profile.allowed_hours_start_ist}:00–{profile.allowed_hours_end_ist}:00 IST. "
            f"Current IST hour is {current_hour}:00."
        )

    return profile


def enforce_host_rate_limit(host: str, min_delay_seconds: float) -> float:
    """Enforce cross-process per-host rate limiting in PostgreSQL (Directive #2).

    Uses a PostgreSQL transaction advisory lock on host hash and plc.host_rate_limit row.
    Returns the number of seconds slept (if any).
    """
    sleep_duration = 0.0

    with transaction.atomic():
        with connection.cursor() as cursor:
            # 1. Advisory transaction lock for this host
            cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtext('host_rate_limit_' || %s));",
                [host],
            )

            # 2. Query last_request_at
            cursor.execute(
                "SELECT last_request_at FROM plc.host_rate_limit WHERE host = %s FOR UPDATE;",
                [host],
            )
            row = cursor.fetchone()

            if row is not None:
                last_request_at = row[0]
                now_utc = datetime.now(UTC)
                elapsed = (now_utc - last_request_at).total_seconds()
                if elapsed < min_delay_seconds:
                    sleep_duration = min_delay_seconds - elapsed
                    time.sleep(sleep_duration)

            # 3. Update or insert host rate limit row
            cursor.execute(
                """
                INSERT INTO plc.host_rate_limit (host, last_request_at, min_delay_seconds)
                VALUES (%s, clock_timestamp(), %s)
                ON CONFLICT (host) DO UPDATE
                SET last_request_at = clock_timestamp(), min_delay_seconds = EXCLUDED.min_delay_seconds;
                """,
                [host, min_delay_seconds],
            )

    return sleep_duration


class GatedHttpClient:
    """Gated HTTP client required for all crawler and source acquisition network calls.

    Passes check_legal_gate() before every request, enforces cross-process rate limiting,
    and applies declared User-Agent.
    """

    def __init__(
        self,
        source_id: str,
        *,
        access_mode: str = "OPEN",
        crawl_mode: str = "delta",
        offline_fixture_resolver: Callable[[str], RawHttpResponse | None] | None = None,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self.source_id = source_id
        self.access_mode = access_mode
        self.crawl_mode = crawl_mode
        self.offline_fixture_resolver = offline_fixture_resolver
        self.now_fn = now_fn or (lambda: datetime.now(UTC))
        self._raw_client: RawHttpClient | None = None

    def _get_raw_client(self) -> RawHttpClient:
        if self._raw_client is None:
            self._raw_client = RawHttpClient()
        return self._raw_client

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
        json: Any = None,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> RawHttpResponse:
        """Issue an HTTP request through the legal gate."""
        # 1. Legal gate check
        now = self.now_fn()
        profile = check_legal_gate(
            source_id=self.source_id,
            access_mode=self.access_mode,
            crawl_mode=self.crawl_mode,
            now=now,
        )

        # 2. Check offline fixture resolver (for deterministic offline testing)
        if self.offline_fixture_resolver is not None:
            fixture_resp = self.offline_fixture_resolver(url)
            if fixture_resp is not None:
                return fixture_resp

        # 3. Cross-process rate limit enforcement (Directive #2)
        parsed_url = urlparse(url)
        host = parsed_url.netloc or self.source_id
        enforce_host_rate_limit(host, profile.rate_limit_delay_seconds)

        # 4. Prepare headers with declared User-Agent (Directive #3)
        req_headers = dict(headers or {})
        ua = getattr(settings, "CRAWLER_USER_AGENT", "")
        contact = getattr(settings, "CRAWLER_CONTACT_EMAIL", "")

        req_headers.setdefault("User-Agent", ua)
        if contact:
            req_headers.setdefault("From", contact)

        # 5. Dispatch via RawHttpClient
        client = self._get_raw_client()
        if method.upper() == "GET":
            return client.get(url, headers=req_headers, params=params, timeout=timeout)
        elif method.upper() == "POST":
            return client.post(url, data=data, json=json, headers=req_headers, timeout=timeout)
        else:
            raise NotImplementedError(
                f"HTTP method '{method}' is not supported by GatedHttpClient."
            )

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> RawHttpResponse:
        return self.request("GET", url, headers=headers, params=params, timeout=timeout)

    def post(
        self,
        url: str,
        *,
        data: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> RawHttpResponse:
        return self.request("POST", url, data=data, json=json, headers=headers, timeout=timeout)

    def close(self) -> None:
        if self._raw_client is not None:
            self._raw_client.close()
            self._raw_client = None

    def __enter__(self) -> GatedHttpClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
