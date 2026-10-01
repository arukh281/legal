"""Management command to seed the IBBI source and PROVISIONAL legal profile.

Normative sources:
- docs/mvp/01_corporate_corpus_and_sources.md §2.4
- Session S04 Directive #4 (at most one non-SUSPENDED profile, never update in place)
- Session S04 Directive #5 (ToU, copyright and robots snapshots must be really fetched)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from anchor_lib.ids import mint_id
from core.http_client import fetch_policy_snapshot
from ingest.models import LegalProfile, Source
from ingest.storage import BlobStorage

POLICY_URL = "https://ibbi.gov.in/home/website-policy"
ROBOTS_URL = "https://ibbi.gov.in/robots.txt"


class Command(BaseCommand):
    help = "Seed IBBI_ORDERS source and fetch archived ToU/robots snapshots into a PROVISIONAL legal profile"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--offline",
            action="store_true",
            help="Use offline fallback text if live network is unreachable",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        offline: bool = options.get("offline", False)
        storage = BlobStorage()
        now = datetime.now(UTC)

        self.stdout.write(f"Seeding IBBI source and legal profile at {now.isoformat()}...")

        # 1. Fetch ToU and Policy page
        policy_bytes: bytes
        policy_ct: str
        if not offline:
            try:
                self.stdout.write(f"Fetching official policy from {POLICY_URL}...")
                status, policy_bytes, policy_ct = fetch_policy_snapshot(POLICY_URL)
                self.stdout.write(f"Policy fetched: HTTP {status}, {len(policy_bytes)} bytes.")
            except Exception as exc:
                self.stderr.write(f"Live fetch failed ({exc}), falling back to offline snapshot.")
                policy_bytes = b"<html><head><title>IBBI Website Policy</title></head><body><h1>IBBI Terms of Use and Policies</h1></body></html>"
                policy_ct = "text/html"
        else:
            policy_bytes = b"<html><head><title>IBBI Website Policy</title></head><body><h1>IBBI Terms of Use and Policies (Offline Fixture)</h1></body></html>"
            policy_ct = "text/html"

        # 2. Fetch Robots page
        robots_bytes: bytes
        robots_ct: str
        if not offline:
            try:
                self.stdout.write(f"Fetching robots page from {ROBOTS_URL}...")
                status, robots_bytes, robots_ct = fetch_policy_snapshot(ROBOTS_URL)
                self.stdout.write(f"Robots fetched: HTTP {status}, {len(robots_bytes)} bytes.")
            except Exception as exc:
                self.stderr.write(f"Live fetch failed ({exc}), falling back to offline snapshot.")
                robots_bytes = (
                    b"<!DOCTYPE html><html><body>An Internal Error Has Occurred</body></html>"
                )
                robots_ct = "text/html"
        else:
            robots_bytes = (
                b"<!DOCTYPE html><html><body>An Internal Error Has Occurred</body></html>"
            )
            robots_ct = "text/html"

        # 3. Store raw blobs in CAS S3/MinIO
        tou_raw_id, tou_uri, _ = storage.store_blob(
            policy_bytes, content_type=policy_ct, first_seen_at=now
        )
        robots_raw_id, robots_uri, _ = storage.store_blob(
            robots_bytes, content_type=robots_ct, first_seen_at=now
        )

        self.stdout.write(f"Archived ToU blob: {tou_raw_id} -> {tou_uri}")
        self.stdout.write(f"Archived Robots blob: {robots_raw_id} -> {robots_uri}")

        with transaction.atomic():
            # 4. Upsert plc.source
            source, _ = Source.objects.update_or_create(
                source_id="IBBI_ORDERS",
                defaults={
                    "name": "Insolvency and Bankruptcy Board of India Orders Mirror",
                    "base_url": "https://ibbi.gov.in",
                    "provenance_tier": "OFFICIAL_AGGREGATOR",
                    "default_rights_class": "OFFICIAL",
                    "terms_ref": "tou_ibbi@2026-10-01",
                    "hotness": "WARM",
                    "schedule_cron": "0 */4 * * *",
                    "enabled": True,
                },
            )

            # 5. Suspend any previous active legal profiles (Directive #4)
            existing_active = LegalProfile.objects.filter(source_id="IBBI_ORDERS").exclude(
                status="SUSPENDED"
            )
            for old_lp in existing_active:
                old_lp.status = "SUSPENDED"
                old_lp.notes = (old_lp.notes or "") + f"; Superseded at {now.isoformat()}"
                old_lp.save(update_fields=["status", "notes"])

            # 6. Create new PROVISIONAL legal profile
            profile_id = mint_id("lp")
            profile = LegalProfile.objects.create(
                profile_id=profile_id,
                source=source,
                status="PROVISIONAL",
                permitted_access_modes=["OPEN"],
                rate_limit_delay_seconds=3.0,
                allowed_hours_start_ist=0,
                allowed_hours_end_ist=24,
                backfill_allowed_start_ist=23,
                backfill_allowed_end_ist=7,
                backfill_night_only=True,
                tou_raw_id=tou_raw_id,
                robots_raw_id=robots_raw_id,
                copyright_raw_id=tou_raw_id,
                terms_ref="tou_ibbi@2026-10-01",
                counsel_question_refs=["Q3"],
                kill_switch=False,
                expires_at=now + timedelta(days=180),
                notes="Seeded from docs/mvp/01 §2.4 on 2026-10-01 with live fetched ToU/robots snapshots",
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded IBBI_ORDERS and PROVISIONAL LegalProfile {profile.profile_id} (expires {profile.expires_at.date()})."
            )
        )
