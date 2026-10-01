"""Tests for Legal Gate governance and profile validation.

Normative sources:
- docs/mvp/01_corporate_corpus_and_sources.md §6.2
- docs/02_P0_source_acquisition.md §5.2
- Session S04 Directive #4 (partial unique index, immutability, midnight wrap)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.db import IntegrityError, transaction

from anchor_lib.ids import mint_id
from ingest.gate import LegalGateViolation, check_legal_gate, is_within_hours
from ingest.models import LegalProfile, RawBlob, Source

IST = ZoneInfo("Asia/Kolkata")


@pytest.fixture
def base_source(db: None) -> Source:
    source, _ = Source.objects.get_or_create(
        source_id="IBBI_TEST_SOURCE",
        defaults={
            "name": "IBBI Test Source",
            "base_url": "https://ibbi.gov.in",
            "provenance_tier": "OFFICIAL_AGGREGATOR",
            "default_rights_class": "OFFICIAL",
            "terms_ref": "tou_ibbi@2026-10-01",
            "hotness": "WARM",
            "enabled": True,
        },
    )
    return source


@pytest.fixture
def sample_blob(db: None) -> RawBlob:
    blob, _ = RawBlob.objects.get_or_create(
        raw_id="sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        defaults={
            "storage_uri": "s3://plc-raw/test.pdf",
            "byte_size": 1024,
            "content_type": "text/html",
            "first_seen_at": datetime.now(UTC),
        },
    )
    return blob


@pytest.mark.django_db
def test_legal_gate_no_profile_fails() -> None:
    """Legal gate strictly blocks any source without an active legal profile."""
    with pytest.raises(LegalGateViolation, match="NO_LEGAL_PROFILE"):
        check_legal_gate(source_id="NON_EXISTENT_SOURCE", access_mode="OPEN")


@pytest.mark.django_db
def test_legal_gate_status_enforcement(base_source: Source, sample_blob: RawBlob) -> None:
    """PROVISIONAL and APPROVED pass; SUSPENDED is blocked."""
    now = datetime.now(UTC)

    # 1. PROVISIONAL profile passes
    lp = LegalProfile.objects.create(
        profile_id=mint_id("lp"),
        source=base_source,
        status="PROVISIONAL",
        permitted_access_modes=["OPEN"],
        rate_limit_delay_seconds=3.0,
        allowed_hours_start_ist=0,
        allowed_hours_end_ist=24,
        tou_raw=sample_blob,
        terms_ref="tou_ibbi@2026-10-01",
        expires_at=now + timedelta(days=90),
    )

    profile = check_legal_gate(source_id=base_source.source_id, access_mode="OPEN", now=now)
    assert profile.profile_id == lp.profile_id

    # 2. APPROVED profile passes
    lp.status = "APPROVED"
    lp.approved_by = "Partner Counsel"
    lp.approved_at = now
    lp.save()

    profile = check_legal_gate(source_id=base_source.source_id, access_mode="OPEN", now=now)
    assert profile.status == "APPROVED"

    # 3. SUSPENDED profile is blocked
    lp.status = "SUSPENDED"
    lp.save()

    with pytest.raises(LegalGateViolation, match="NO_LEGAL_PROFILE"):
        check_legal_gate(source_id=base_source.source_id, access_mode="OPEN", now=now)


@pytest.mark.django_db
def test_legal_gate_expiration_enforcement(base_source: Source, sample_blob: RawBlob) -> None:
    """Profile past expires_at is strictly blocked."""
    now = datetime.now(UTC)

    LegalProfile.objects.create(
        profile_id=mint_id("lp"),
        source=base_source,
        status="PROVISIONAL",
        permitted_access_modes=["OPEN"],
        rate_limit_delay_seconds=3.0,
        allowed_hours_start_ist=0,
        allowed_hours_end_ist=24,
        tou_raw=sample_blob,
        terms_ref="tou_ibbi@2026-10-01",
        expires_at=now - timedelta(seconds=1),  # Expired
    )

    with pytest.raises(LegalGateViolation, match="PROFILE_EXPIRED"):
        check_legal_gate(source_id=base_source.source_id, access_mode="OPEN", now=now)


@pytest.mark.django_db
def test_legal_gate_kill_switch_enforcement(base_source: Source, sample_blob: RawBlob) -> None:
    """Kill switch instantly halts all network access."""
    now = datetime.now(UTC)

    LegalProfile.objects.create(
        profile_id=mint_id("lp"),
        source=base_source,
        status="PROVISIONAL",
        permitted_access_modes=["OPEN"],
        rate_limit_delay_seconds=3.0,
        allowed_hours_start_ist=0,
        allowed_hours_end_ist=24,
        tou_raw=sample_blob,
        terms_ref="tou_ibbi@2026-10-01",
        expires_at=now + timedelta(days=90),
        kill_switch=True,
        kill_reason="Legal dispute ongoing",
    )

    with pytest.raises(LegalGateViolation, match="KILL_SWITCH_ACTIVE"):
        check_legal_gate(source_id=base_source.source_id, access_mode="OPEN", now=now)


@pytest.mark.django_db
def test_legal_gate_permitted_access_modes(base_source: Source, sample_blob: RawBlob) -> None:
    """Access modes not explicitly listed in profile are blocked."""
    now = datetime.now(UTC)

    LegalProfile.objects.create(
        profile_id=mint_id("lp"),
        source=base_source,
        status="PROVISIONAL",
        permitted_access_modes=["OPEN"],
        rate_limit_delay_seconds=3.0,
        allowed_hours_start_ist=0,
        allowed_hours_end_ist=24,
        tou_raw=sample_blob,
        terms_ref="tou_ibbi@2026-10-01",
        expires_at=now + timedelta(days=90),
    )

    # OPEN is permitted
    assert (
        check_legal_gate(source_id=base_source.source_id, access_mode="OPEN", now=now) is not None
    )

    # BULK_DATASET or LICENSED_API is blocked
    with pytest.raises(LegalGateViolation, match="ACCESS_MODE_NOT_PERMITTED"):
        check_legal_gate(source_id=base_source.source_id, access_mode="BULK_DATASET", now=now)

    with pytest.raises(LegalGateViolation, match="ACCESS_MODE_NOT_PERMITTED"):
        check_legal_gate(source_id=base_source.source_id, access_mode="LICENSED_API", now=now)


def test_is_within_hours_midnight_wrap() -> None:
    """Test midnight-wrapping hour calculation (Directive #4).

    Window: 23:00 to 07:00 IST (night only).
    """
    start = 23
    end = 7

    # Night hours should be within window
    assert is_within_hours(23, start, end) is True
    assert is_within_hours(0, start, end) is True
    assert is_within_hours(1, start, end) is True
    assert is_within_hours(3, start, end) is True
    assert is_within_hours(6, start, end) is True

    # Daytime hours should be outside window
    assert is_within_hours(7, start, end) is False
    assert is_within_hours(8, start, end) is False
    assert is_within_hours(12, start, end) is False
    assert is_within_hours(14, start, end) is False
    assert is_within_hours(22, start, end) is False


@pytest.mark.django_db
def test_backfill_mode_restricts_to_night_ist(base_source: Source, sample_blob: RawBlob) -> None:
    """Backfill crawl mode is blocked during daytime IST and permitted at night IST."""
    base_date = datetime(2026, 10, 1, 0, 0, 0, tzinfo=UTC)

    LegalProfile.objects.create(
        profile_id=mint_id("lp"),
        source=base_source,
        status="PROVISIONAL",
        permitted_access_modes=["OPEN"],
        rate_limit_delay_seconds=3.0,
        allowed_hours_start_ist=0,
        allowed_hours_end_ist=24,
        backfill_allowed_start_ist=23,
        backfill_allowed_end_ist=7,
        backfill_night_only=True,
        tou_raw=sample_blob,
        terms_ref="tou_ibbi@2026-10-01",
        expires_at=base_date + timedelta(days=120),
    )

    # 14:00 IST = 08:30 UTC -> Daytime in India -> Backfill must be BLOCKED
    day_utc = datetime(2026, 10, 1, 8, 30, 0, tzinfo=UTC)
    assert day_utc.astimezone(IST).hour == 14

    with pytest.raises(LegalGateViolation, match="OUTSIDE_ALLOWED_HOURS"):
        check_legal_gate(
            source_id=base_source.source_id,
            access_mode="OPEN",
            crawl_mode="backfill",
            now=day_utc,
        )

    # Delta mode still passes during daytime
    delta_profile = check_legal_gate(
        source_id=base_source.source_id,
        access_mode="OPEN",
        crawl_mode="delta",
        now=day_utc,
    )
    assert delta_profile is not None

    # 02:00 IST = 20:30 UTC previous day -> Night in India -> Backfill passes
    night_utc = datetime(2026, 9, 30, 20, 30, 0, tzinfo=UTC)
    assert night_utc.astimezone(IST).hour == 2

    backfill_profile = check_legal_gate(
        source_id=base_source.source_id,
        access_mode="OPEN",
        crawl_mode="backfill",
        now=night_utc,
    )
    assert backfill_profile is not None


@pytest.mark.django_db
def test_partial_unique_index_and_superseding(base_source: Source, sample_blob: RawBlob) -> None:
    """Verify at most one non-SUSPENDED profile per source (Directive #4)."""
    now = datetime.now(UTC)

    # 1. Create first profile
    lp1 = LegalProfile.objects.create(
        profile_id=mint_id("lp"),
        source=base_source,
        status="PROVISIONAL",
        permitted_access_modes=["OPEN"],
        rate_limit_delay_seconds=3.0,
        allowed_hours_start_ist=0,
        allowed_hours_end_ist=24,
        tou_raw=sample_blob,
        terms_ref="tou_ibbi@2026-10-01",
        expires_at=now + timedelta(days=90),
    )

    # 2. Attempting to create a second non-SUSPENDED profile raises IntegrityError
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            LegalProfile.objects.create(
                profile_id=mint_id("lp"),
                source=base_source,
                status="PROVISIONAL",
                permitted_access_modes=["OPEN"],
                rate_limit_delay_seconds=3.0,
                allowed_hours_start_ist=0,
                allowed_hours_end_ist=24,
                tou_raw=sample_blob,
                terms_ref="tou_ibbi@2026-10-01",
                expires_at=now + timedelta(days=90),
            )

    # 3. Suspend first profile, then create new profile -> succeeds
    lp1.status = "SUSPENDED"
    lp1.save()

    lp2 = LegalProfile.objects.create(
        profile_id=mint_id("lp"),
        source=base_source,
        status="APPROVED",
        approved_by="Partner Counsel",
        approved_at=now,
        permitted_access_modes=["OPEN"],
        rate_limit_delay_seconds=2.0,
        allowed_hours_start_ist=0,
        allowed_hours_end_ist=24,
        tou_raw=sample_blob,
        terms_ref="tou_ibbi@2026-10-01",
        expires_at=now + timedelta(days=180),
    )

    active_profile = check_legal_gate(source_id=base_source.source_id, access_mode="OPEN", now=now)
    assert active_profile.profile_id == lp2.profile_id
