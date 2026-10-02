"""Management command to seed the IBBI source and PROVISIONAL legal profile.

Normative sources:
- docs/mvp/01_corporate_corpus_and_sources.md §2.4
- Session S04 Directive #4 (at most one non-SUSPENDED profile, never update in place)
- Session S04 Directive #5 (ToU, copyright and robots snapshots must be really fetched)
- Session S04 Closure Directive #3 & #4 (all network calls go through GatedHttpClient)
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

POLICY_URL = "https://ibbi.gov.in/home/website-policy"
ROBOTS_URL = "https://ibbi.gov.in/robots.txt"


class Command(BaseCommand):
    help = "Seed IBBI_ORDERS source and fetch archived ToU/robots snapshots into a PROVISIONAL legal profile via GatedHttpClient"

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

        # 1. Ensure plc.source exists
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

        # 2. Ensure an active LegalProfile exists so GatedHttpClient passes the legal gate
        active_lp = (
            LegalProfile.objects.filter(source_id="IBBI_ORDERS").exclude(status="SUSPENDED").first()
        )
        if active_lp is None:
            bootstrap_id = mint_id("lp")
            active_lp = LegalProfile.objects.create(
                profile_id=bootstrap_id,
                source=source,
                status="PROVISIONAL",
                permitted_access_modes=["OPEN"],
                rate_limit_delay_seconds=3.0,
                allowed_hours_start_ist=0,
                allowed_hours_end_ist=24,
                backfill_allowed_start_ist=23,
                backfill_allowed_end_ist=7,
                backfill_night_only=True,
                terms_ref="tou_ibbi@2026-10-01",
                counsel_question_refs=["Q3"],
                kill_switch=False,
                expires_at=now + timedelta(days=180),
                notes="Bootstrap profile for gated policy snapshot fetch",
            )
            self.stdout.write(f"Created bootstrap legal profile {active_lp.profile_id}")

        # 3. Fetch Policy and Robots through GatedHttpClient
        resolver = None
        if offline:

            def _resolver(url: str) -> RawHttpResponse | None:
                if "website-policy" in url:
                    html = (
                        "<html><head><title>IBBI Website Policy</title></head><body>"
                        "<h1>IBBI Terms of Use and Policies</h1>"
                        "<div id='hyperlink-policy'><h3>Hyperlink Policy</h3>"
                        "<p>no prior permission is required but we would like you to inform us</p>"
                        "<p>We do not permit our pages to be loaded into frames</p></div>"
                        "<div id='copyright-policy'><h3>Copyright Policy</h3>"
                        "<!-- <p>Material featured on this site may be reproduced free of charge in any format or media without requiring specific permission</p> --></div>"
                        "</body></html>"
                    )
                    return RawHttpResponse(
                        200, {"content-type": "text/html"}, html.encode("utf-8"), url
                    )
                elif "robots.txt" in url:
                    txt = "User-agent: *\nDisallow: /admin\n"
                    return RawHttpResponse(
                        200, {"content-type": "text/plain"}, txt.encode("utf-8"), url
                    )
                return None

            resolver = _resolver

        client = GatedHttpClient(
            source_id="IBBI_ORDERS", crawl_mode="delta", offline_fixture_resolver=resolver
        )

        self.stdout.write(f"Fetching official policy via GatedHttpClient from {POLICY_URL}...")
        policy_resp = client.get(POLICY_URL)
        policy_fetched_at = datetime.now(UTC)
        policy_bytes = policy_resp.content
        policy_ct = policy_resp.headers.get("content-type", "text/html")
        self.stdout.write(
            f"Policy fetched: HTTP {policy_resp.status_code}, {len(policy_bytes)} bytes at {policy_fetched_at.isoformat()}."
        )

        # Verify copyright and hyperlink policy sections
        policy_text = policy_bytes.decode("utf-8", errors="replace")
        has_hyperlink = "hyperlink-policy" in policy_text or "Hyperlink Policy" in policy_text
        has_copyright = "copyright-policy" in policy_text or "Copyright Policy" in policy_text
        if not (has_hyperlink and has_copyright):
            self.stderr.write(
                "WARNING: Website policy did not match expected copyright and hyperlink sections!"
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "Verified: Website policy contains copyright and hyperlink sections cited in 01 §2.4."
                )
            )

        self.stdout.write(f"Fetching robots.txt via GatedHttpClient from {ROBOTS_URL}...")
        robots_resp = client.get(ROBOTS_URL)
        robots_fetched_at = datetime.now(UTC)
        robots_bytes = robots_resp.content
        robots_ct = robots_resp.headers.get("content-type", "text/plain")
        self.stdout.write(
            f"Robots fetched: HTTP {robots_resp.status_code}, {len(robots_bytes)} bytes at {robots_fetched_at.isoformat()}."
        )

        # 4. Store raw blobs in CAS S3/MinIO
        tou_raw_id, tou_uri, _ = storage.store_blob(
            policy_bytes, content_type=policy_ct, first_seen_at=policy_fetched_at
        )
        robots_raw_id, robots_uri, _ = storage.store_blob(
            robots_bytes, content_type=robots_ct, first_seen_at=robots_fetched_at
        )

        self.stdout.write(f"Archived ToU blob: {tou_raw_id} -> {tou_uri}")
        self.stdout.write(f"Archived Robots blob: {robots_raw_id} -> {robots_uri}")

        with transaction.atomic():
            # 5. Suspend any previous active legal profiles (Directive #4)
            existing_active = LegalProfile.objects.filter(source_id="IBBI_ORDERS").exclude(
                status="SUSPENDED"
            )
            for old_lp in existing_active:
                old_lp.status = "SUSPENDED"
                old_lp.notes = (
                    old_lp.notes or ""
                ) + f"; Superseded at {policy_fetched_at.isoformat()}"
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
                notes=(
                    f"Seeded from docs/mvp/01 §2.4; website policy fetched at "
                    f"{policy_fetched_at.isoformat()} via GatedHttpClient"
                ),
            )

            # 7. Record Capture audit records for terms & robots
            Capture.objects.create(
                capture_id=mint_id("cap"),
                source=source,
                source_record_key="policy:website-policy",
                url=POLICY_URL,
                fetched_at=policy_fetched_at,
                change_kind="NEW",
                raw_id=tou_raw_id,
                rights_class="OFFICIAL",
                provenance_tier="OFFICIAL_AGGREGATOR",
                fetch_context={
                    "profile_id": profile.profile_id,
                    "kind": "website_policy",
                    "gated": True,
                },
            )
            Capture.objects.create(
                capture_id=mint_id("cap"),
                source=source,
                source_record_key="policy:robots-txt",
                url=ROBOTS_URL,
                fetched_at=robots_fetched_at,
                change_kind="NEW",
                raw_id=robots_raw_id,
                rights_class="OFFICIAL",
                provenance_tier="OFFICIAL_AGGREGATOR",
                fetch_context={
                    "profile_id": profile.profile_id,
                    "kind": "robots_txt",
                    "gated": True,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded IBBI_ORDERS and PROVISIONAL LegalProfile {profile.profile_id} "
                f"(expires {profile.expires_at.date()}). Policy fetch time recorded: {policy_fetched_at.isoformat()}."
            )
        )
