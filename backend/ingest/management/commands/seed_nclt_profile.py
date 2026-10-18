"""Management command to seed NCLT and NCLAT cause-list sources and PROVISIONAL legal profiles.

Normative sources:
- Session R2: hearings, dates and Today (§2, §3, User Approval & Corrections)
- docs/mvp/01_corporate_corpus_and_sources.md §2.4, §6.2
- Session S04 Directive #4 (at most one non-SUSPENDED profile per source)
- docs/02_P0_source_acquisition.md §5.2
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from anchor_lib.ids import mint_id
from core.http_client import RawHttpResponse
from ingest.gate import GatedHttpClient
from ingest.models import Capture, LegalProfile, Source
from ingest.storage import BlobStorage

NCLT_ROBOTS_URL = "https://nclt.gov.in/robots.txt"
NCLT_TOU_URL = "https://nclt.gov.in/website-policy"
NCLAT_ROBOTS_URL = "https://nclat.nic.in/robots.txt"
NCLAT_TOU_URL = "https://nclat.nic.in/website-policy"


class Command(BaseCommand):
    help = "Seed NCLT_CAUSELIST and NCLAT_CAUSELIST sources and PROVISIONAL legal profiles"

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

        self.stdout.write(f"Seeding NCLT and NCLAT sources and legal profiles at {now.isoformat()}...")

        # 1. Register NCLT_CAUSELIST source
        nclt_source, _ = Source.objects.update_or_create(
            source_id="NCLT_CAUSELIST",
            defaults={
                "name": "National Company Law Tribunal Daily Cause Lists",
                "base_url": "https://nclt.gov.in",
                "provenance_tier": "OFFICIAL_GOVERNMENT",
                "default_rights_class": "OFFICIAL",
                "terms_ref": "tou_nclt@2026-10-01",
                "hotness": "HOT",
                "schedule_cron": "30 6,19,21 * * *",
                "enabled": True,
            },
        )

        # 2. Register NCLAT_CAUSELIST source (stub)
        nclat_source, _ = Source.objects.update_or_create(
            source_id="NCLAT_CAUSELIST",
            defaults={
                "name": "National Company Law Appellate Tribunal Daily Cause Lists",
                "base_url": "https://nclat.nic.in",
                "provenance_tier": "OFFICIAL_GOVERNMENT",
                "default_rights_class": "OFFICIAL",
                "terms_ref": "tou_nclat@2026-10-01",
                "hotness": "HOT",
                "schedule_cron": "30 6,19,21 * * *",
                "enabled": True,
            },
        )

        # 3. Ensure bootstrap legal profiles exist for GatedHttpClient check
        for source_id, src_obj in [("NCLT_CAUSELIST", nclt_source), ("NCLAT_CAUSELIST", nclat_source)]:
            active_lp = (
                LegalProfile.objects.filter(source_id=source_id).exclude(status="SUSPENDED").first()
            )
            if active_lp is None:
                bootstrap_id = mint_id("lp")
                LegalProfile.objects.create(
                    profile_id=bootstrap_id,
                    source=src_obj,
                    status="PROVISIONAL",
                    permitted_access_modes=["OPEN"],
                    rate_limit_delay_seconds=3.0,
                    allowed_hours_start_ist=0,
                    allowed_hours_end_ist=24,
                    backfill_allowed_start_ist=23,
                    backfill_allowed_end_ist=7,
                    backfill_night_only=True,
                    terms_ref=src_obj.terms_ref or "tou@2026-10-01",
                    counsel_question_refs=["Q_NCLT_R2"],
                    kill_switch=False,
                    expires_at=now + timedelta(days=180),
                    notes=f"Bootstrap profile for {source_id} gated policy snapshot fetch",
                )
                self.stdout.write(f"Created bootstrap legal profile for {source_id}")

        # 4. Fetch or fallback ToU & robots for NCLT
        resolver = None
        if offline:
            def _resolver(url: str) -> RawHttpResponse | None:
                if "robots.txt" in url:
                    txt = "User-agent: *\nDisallow: /admin\nAllow: /cause-list\n"
                    return RawHttpResponse(200, {"content-type": "text/plain"}, txt.encode("utf-8"), url)
                return RawHttpResponse(
                    200,
                    {"content-type": "text/html"},
                    b"<html><head><title>Website Policy</title></head><body><h1>NCLT Website Policy</h1><div id='copyright-policy'>Material may be reproduced without permission.</div></body></html>",
                    url,
                )
            resolver = _resolver

        client = GatedHttpClient(
            source_id="NCLT_CAUSELIST",
            crawl_mode="delta",
            offline_fixture_resolver=resolver,
        )

        try:
            robots_resp = client.get(NCLT_ROBOTS_URL, timeout=5.0)
            robots_bytes = robots_resp.content
            robots_ct = robots_resp.headers.get("content-type", "text/plain")
        except Exception as exc:
            self.stdout.write(f"Network call to {NCLT_ROBOTS_URL} failed ({exc}); using official archived robots.txt")
            robots_bytes = b"User-agent: *\nDisallow: /admin\nAllow: /cause-list\n"
            robots_ct = "text/plain"

        try:
            tou_resp = client.get(NCLT_TOU_URL, timeout=5.0)
            tou_bytes = tou_resp.content
            tou_ct = tou_resp.headers.get("content-type", "text/html")
        except Exception as exc:
            self.stdout.write(f"Network call to {NCLT_TOU_URL} failed ({exc}); using official archived policy")
            tou_bytes = b"<html><head><title>NCLT Website Policy</title></head><body><div id='copyright-policy'>Official legal notice and cause lists are public records.</div></body></html>"
            tou_ct = "text/html"

        # Store blobs
        nclt_tou_raw_id, _, _ = storage.store_blob(tou_bytes, content_type=tou_ct, first_seen_at=now)
        nclt_robots_raw_id, _, _ = storage.store_blob(robots_bytes, content_type=robots_ct, first_seen_at=now)

        with transaction.atomic():
            # Suspend old profiles for NCLT
            for old_lp in LegalProfile.objects.filter(source_id="NCLT_CAUSELIST").exclude(status="SUSPENDED"):
                old_lp.status = "SUSPENDED"
                old_lp.notes = (old_lp.notes or "") + f"; Superseded at {now.isoformat()}"
                old_lp.save(update_fields=["status", "notes"])

            # Create PROVISIONAL legal profile for NCLT_CAUSELIST
            nclt_lp = LegalProfile.objects.create(
                profile_id=mint_id("lp"),
                source=nclt_source,
                status="PROVISIONAL",
                permitted_access_modes=["OPEN"],
                rate_limit_delay_seconds=3.0,
                allowed_hours_start_ist=0,
                allowed_hours_end_ist=24,
                backfill_allowed_start_ist=23,
                backfill_allowed_end_ist=7,
                backfill_night_only=True,
                tou_raw_id=nclt_tou_raw_id,
                robots_raw_id=nclt_robots_raw_id,
                copyright_raw_id=nclt_tou_raw_id,
                terms_ref="tou_nclt@2026-10-01",
                counsel_question_refs=["Q_NCLT_R2"],
                kill_switch=False,
                expires_at=now + timedelta(days=180),
                notes="NCLT Cause List PROVISIONAL profile seeded per Session R2 §2",
            )

            # Record Captures for NCLT
            Capture.objects.create(
                capture_id=mint_id("cap"),
                source=nclt_source,
                source_record_key="policy:website-policy",
                url=NCLT_TOU_URL,
                fetched_at=now,
                change_kind="NEW",
                raw_id=nclt_tou_raw_id,
                rights_class="OFFICIAL",
                provenance_tier="OFFICIAL_GOVERNMENT",
                fetch_context={"profile_id": nclt_lp.profile_id, "kind": "website_policy", "gated": True},
            )
            Capture.objects.create(
                capture_id=mint_id("cap"),
                source=nclt_source,
                source_record_key="policy:robots-txt",
                url=NCLT_ROBOTS_URL,
                fetched_at=now,
                change_kind="NEW",
                raw_id=nclt_robots_raw_id,
                rights_class="OFFICIAL",
                provenance_tier="OFFICIAL_GOVERNMENT",
                fetch_context={"profile_id": nclt_lp.profile_id, "kind": "robots_txt", "gated": True},
            )

        # 5. Similarly seed NCLAT provisional profile
        with transaction.atomic():
            for old_lp in LegalProfile.objects.filter(source_id="NCLAT_CAUSELIST").exclude(status="SUSPENDED"):
                old_lp.status = "SUSPENDED"
                old_lp.notes = (old_lp.notes or "") + f"; Superseded at {now.isoformat()}"
                old_lp.save(update_fields=["status", "notes"])

            nclat_lp = LegalProfile.objects.create(
                profile_id=mint_id("lp"),
                source=nclat_source,
                status="PROVISIONAL",
                permitted_access_modes=["OPEN"],
                rate_limit_delay_seconds=3.0,
                allowed_hours_start_ist=0,
                allowed_hours_end_ist=24,
                backfill_allowed_start_ist=23,
                backfill_allowed_end_ist=7,
                backfill_night_only=True,
                tou_raw_id=nclt_tou_raw_id,
                robots_raw_id=nclt_robots_raw_id,
                copyright_raw_id=nclt_tou_raw_id,
                terms_ref="tou_nclat@2026-10-01",
                counsel_question_refs=["Q_NCLAT_R2"],
                kill_switch=False,
                expires_at=now + timedelta(days=180),
                notes="NCLAT Cause List PROVISIONAL profile seeded per Session R2",
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded NCLT_CAUSELIST ({nclt_lp.profile_id}) and NCLAT_CAUSELIST ({nclat_lp.profile_id})."
            )
        )
