"""Probe NCLAT cause-list page via GatedHttpClient and record findings.

Normative source:
- Session R2: hearings, dates and Today (User answer 5:
  'In the live run, fetch the NCLAT cause-list page once through GatedHttpClient
   and record what it actually serves, so the next session can decide.')
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from ingest.gate import GatedHttpClient


class Command(BaseCommand):
    help = "Probe NCLAT cause list URL through GatedHttpClient and save results"

    def handle(self, *args: Any, **options: Any) -> None:
        client = GatedHttpClient(source_id="NCLAT_CAUSELIST", crawl_mode="delta")
        probe_urls = [
            "https://nclat.nic.in/cause-list",
            "https://nclat.nic.in",
        ]
        results: list[dict[str, Any]] = []

        for target_url in probe_urls:
            self.stdout.write(f"Probing {target_url} via GatedHttpClient...")
            try:
                resp = client.request("GET", target_url, timeout=10.0)
                results.append({
                    "url": target_url,
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers),
                    "content_length": len(resp.content),
                    "body_snippet": resp.text[:2000],
                    "timestamp": datetime.now(UTC).isoformat(),
                    "success": True,
                })
                self.stdout.write(f"Result for {target_url}: HTTP {resp.status_code}, {len(resp.content)} bytes")
            except Exception as exc:
                self.stdout.write(f"Probe failed for {target_url}: {exc}")
                results.append({
                    "url": target_url,
                    "error": str(exc),
                    "timestamp": datetime.now(UTC).isoformat(),
                    "success": False,
                })

        output_path = Path("/Users/aradhyakhandelwal/Desktop/Work/lawyer_brain/eval/fixtures/nclat_probe.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Saved NCLAT probe findings to {output_path}"))
