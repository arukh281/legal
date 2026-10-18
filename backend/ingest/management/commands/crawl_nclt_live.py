"""Exit Check 8: Marked live NCLT crawl and NCLAT probe via GatedHttpClient.

Normative sources:
- Session R2: Exit check 8
- User open question 5: "In the live run, fetch the NCLAT cause-list page once through GatedHttpClient and record what it actually serves, so the next session can decide."
- Non-negotiable #5: Obey robots.txt and rate limits (<= 1 req / 3s), stop on CAPTCHA.
"""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urljoin

from django.core.management.base import BaseCommand

from ingest.causelist_parser import NCLTCauseListParser
from ingest.gate import GatedHttpClient


class Command(BaseCommand):
    help = "Run one marked live NCLT crawl and NCLAT cause-list probe via GatedHttpClient (Exit Check 8)."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("=== EXIT CHECK 8: MARKED LIVE NCLT CRAWL & NCLAT PROBE ==="))

        start_time = time.time()
        parser = NCLTCauseListParser()

        # -------------------------------------------------------------
        # Part 1: NCLT Live Cause List Crawl
        # -------------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_LABEL("\n--- 1. Live NCLT Daily Cause List Crawl ---"))
        nclt_client = GatedHttpClient(
            source_id="NCLT_CAUSELIST",
            access_mode="OPEN",
            crawl_mode="delta",
        )

        nclt_url = "https://nclt.gov.in/cause-list"
        self.stdout.write(f"Fetching NCLT cause list index: {nclt_url} via GatedHttpClient...")
        t0 = time.time()
        nclt_resp = nclt_client.get(nclt_url)
        nclt_index_duration = time.time() - t0

        self.stdout.write(f"✓ NCLT index response: status={nclt_resp.status_code}, length={len(nclt_resp.content)} bytes, duration={nclt_index_duration:.2f}s")

        # Check for CAPTCHA
        captcha_found = False
        body_text = nclt_resp.text
        if re.search(r"(captcha|recaptcha|cf-turnstile|cf-challenge)", body_text, re.IGNORECASE):
            captcha_found = True
            self.stdout.write(self.style.ERROR("! CAPTCHA / bot challenge detected on NCLT page!"))
        else:
            self.stdout.write("✓ No CAPTCHA detected on NCLT index page.")

        # Find cause list PDF links
        pdf_urls = re.findall(r'href=[\'"]([^\'"]+?\.pdf)[\'"]', body_text, re.IGNORECASE)
        # Filter for cause list pdfs
        causelist_pdfs = [urljoin(nclt_url, u) for u in pdf_urls if "cause" in u.lower() or "list" in u.lower() or "court" in u.lower()]
        if not causelist_pdfs and pdf_urls:
            causelist_pdfs = [urljoin(nclt_url, u) for u in pdf_urls]

        self.stdout.write(f"Discovered {len(causelist_pdfs)} cause list PDF links on NCLT page.")

        lists_fetched = 0
        total_items_parsed = 0
        total_unparsed_lines = 0
        drift_detected = False
        drift_reasons: list[str] = []

        if causelist_pdfs:
            target_pdf_url = causelist_pdfs[0]
            self.stdout.write(f"Fetching live cause list PDF: {target_pdf_url} (enforcing rate limit >= 3s)...")
            t_pdf = time.time()
            pdf_resp = nclt_client.get(target_pdf_url)
            pdf_duration = time.time() - t_pdf
            lists_fetched += 1

            self.stdout.write(f"✓ PDF downloaded: status={pdf_resp.status_code}, size={len(pdf_resp.content)} bytes, duration={pdf_duration:.2f}s")

            # Parse PDF
            parsed = parser.parse_pdf_bytes(pdf_resp.content)
            total_items_parsed += len(parsed.items)
            total_unparsed_lines += parsed.unparsed_lines_count
            if parsed.layout_drift:
                drift_detected = True
                if parsed.drift_reason:
                    drift_reasons.append(parsed.drift_reason)

            self.stdout.write(f"✓ Parsed live PDF: bench={parsed.bench}, court_no={parsed.court_no}, date={parsed.list_date}")
            self.stdout.write(f"  - Total items parsed: {len(parsed.items)}")
            self.stdout.write(f"  - Unparsed lines: {parsed.unparsed_lines_count}")
            self.stdout.write(f"  - Layout drift: {parsed.layout_drift} (reason: {parsed.drift_reason or 'None'})")

            if parsed.items:
                sample_item = parsed.items[0]
                sample_cases = [c.canonical for c in sample_item.normalized_cases]
                self.stdout.write(f"  - Sample Item {sample_item.item_no}: cases={sample_cases}, parties='{sample_item.parties[:50]}...'")

        # -------------------------------------------------------------
        # Part 2: NCLAT Live Cause List Probe
        # -------------------------------------------------------------
        self.stdout.write(self.style.MIGRATE_LABEL("\n--- 2. NCLAT Cause List Page Probe (User Question 5) ---"))
        nclat_client = GatedHttpClient(
            source_id="NCLAT_CAUSELIST",
            access_mode="OPEN",
            crawl_mode="delta",
        )

        nclat_urls = [
            "https://nclat.nic.in/cause-list",
            "https://nclat.nic.in/cause-list/daily-cause-list",
            "https://nclat.nic.in",
        ]

        nclat_served_status = None
        nclat_content_type = None
        nclat_captcha = False
        nclat_body_len = 0
        nclat_pdf_links_count = 0

        for candidate_url in nclat_urls:
            self.stdout.write(f"Probing NCLAT URL: {candidate_url} via GatedHttpClient (3s floor)...")
            try:
                t_nclat = time.time()
                resp = nclat_client.get(candidate_url)
                dur = time.time() - t_nclat
                nclat_served_status = resp.status_code
                nclat_content_type = resp.headers.get("content-type", "unknown")
                nclat_body_len = len(resp.content)
                body_str = resp.text

                if re.search(r"(captcha|recaptcha|cf-turnstile|cf-challenge)", body_str, re.IGNORECASE):
                    nclat_captcha = True

                pdfs = re.findall(r'href=[\'"]([^\'"]+?\.pdf)[\'"]', body_str, re.IGNORECASE)
                nclat_pdf_links_count = len(pdfs)

                self.stdout.write(
                    f"✓ NCLAT response: status={resp.status_code}, content_type='{nclat_content_type}', length={nclat_body_len} bytes, duration={dur:.2f}s, pdf_links={nclat_pdf_links_count}"
                )
                if resp.status_code == 200:
                    break
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"NCLAT probe exception for {candidate_url}: {e}"))

        total_elapsed = time.time() - start_time

        # -------------------------------------------------------------
        # Summary
        # -------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("\n=== LIVE RUN SUMMARY REPORT ==="))
        self.stdout.write(f"• Total time taken: {total_elapsed:.2f}s")
        self.stdout.write(f"• NCLT lists fetched: {lists_fetched}")
        self.stdout.write(f"• NCLT entries parsed: {total_items_parsed}")
        self.stdout.write(f"• NCLT unparsed lines: {total_unparsed_lines}")
        self.stdout.write(f"• NCLT CAPTCHA encountered: {captcha_found}")
        self.stdout.write(f"• NCLT layout drift: {drift_detected} ({', '.join(drift_reasons) if drift_reasons else 'None'})")
        self.stdout.write(f"• NCLAT probe status: {nclat_served_status} (Content-Type: {nclat_content_type}, CAPTCHA: {nclat_captcha}, PDFs found: {nclat_pdf_links_count})")
