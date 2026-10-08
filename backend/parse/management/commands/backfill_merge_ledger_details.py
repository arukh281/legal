"""Management command to backfill details jsonb on historical IdentityMergeLedger rows.

Normative sources:
- AGENTS.md §4 & §5 (Non-negotiables: bitemporal Assertion ledger, zero deletions)
- docs/mvp/03_data_model_and_contracts.md §3.3 (plc.identity_merge_ledger)
- S05b Follow-up directive:
  - op=MERGE, kind=WORK, reason=REPARSE_DUPLICATE_RAW_BLOB and details IS NULL
  - Abort with CommandError if row count is not 346 or any from_id is missing from s05b report
  - Print counts by prior_status (expect 294 ACTIVE, 52 PROVISIONAL)
  - Default to --dry-run (no writes) unless --no-dry-run or --commit is passed
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from parse.models import IdentityMergeLedger


class Command(BaseCommand):
    help = "Backfill details on historical IdentityMergeLedger rows from s05b report inventory."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Simulate backfill without writing to database (default: True). Use --no-dry-run to commit.",
        )
        parser.add_argument(
            "--commit",
            action="store_true",
            default=False,
            help="Commit backfill changes to the database (equivalent to --no-dry-run).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = options.get("dry_run", True)
        if options.get("commit", False):
            dry_run = False

        self.stdout.write(self.style.NOTICE("=== Starting Merge Ledger Details Backfill ==="))
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE: No writes will be committed."))

        # 1. Locate s05b orphan works report
        report_path = None
        for candidate in [
            Path("eval/reports/s05b_orphan_works_report.txt"),
            Path("../eval/reports/s05b_orphan_works_report.txt"),
        ]:
            if candidate.exists():
                report_path = candidate
                break

        if not report_path:
            raise CommandError(
                "Could not find eval/reports/s05b_orphan_works_report.txt. Aborting."
            )

        # 2. Parse report inventory (from_id -> prior_status)
        report_inventory: dict[str, str] = {}
        for line in report_path.read_text().splitlines():
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 6 and parts[2].startswith("wrk_"):
                    report_inventory[parts[2]] = parts[5]

        self.stdout.write(f"Loaded {len(report_inventory)} inventory records from {report_path}.")

        with transaction.atomic():
            # 3. Query target rows: op=MERGE, kind=WORK, reason=REPARSE_DUPLICATE_RAW_BLOB, details IS NULL
            target_qs = IdentityMergeLedger.objects.select_for_update().filter(
                op="MERGE",
                kind="WORK",
                reason="REPARSE_DUPLICATE_RAW_BLOB",
                details__isnull=True,
            )
            target_count = target_qs.count()

            self.stdout.write(f"Found {target_count} target rows with details IS NULL.")

            if target_count != 346:
                raise CommandError(
                    f"Target row count mismatch: expected exactly 346 rows, found {target_count}. Aborting without writes."
                )

            # 4. Validate that all from_ids exist in the report inventory (no fallback to ACTIVE!)
            missing_ids: list[str] = []
            status_counts: Counter[str] = Counter()
            updates: list[tuple[IdentityMergeLedger, dict[str, Any]]] = []

            for ledger in target_qs:
                if ledger.from_id not in report_inventory:
                    missing_ids.append(ledger.from_id)
                else:
                    prior_status = report_inventory[ledger.from_id]
                    status_counts[prior_status] += 1
                    new_details = {
                        "prior_status": prior_status,
                        "superseded_alias_ids": [],
                        "retargeted_alias_ids": [],
                        "repointed_mention_ids": [],
                    }
                    updates.append((ledger, new_details))

            if missing_ids:
                raise CommandError(
                    f"Found {len(missing_ids)} from_ids missing from s05b report: {missing_ids[:5]}... Aborting without writes."
                )

            # 5. Print counts by prior_status
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write("--- PRIOR STATUS BREAKDOWN ---")
            self.stdout.write("=" * 50)
            for status, count in sorted(status_counts.items()):
                self.stdout.write(f"  {status}: {count}")
            self.stdout.write("=" * 50 + "\n")

            # 6. Apply updates
            for ledger, new_details in updates:
                ledger.details = new_details
                ledger.save(update_fields=["details"])

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING(
                        f"[DRY RUN] Rolled back {len(updates)} details backfill updates cleanly."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully backfilled details on {len(updates)} IdentityMergeLedger rows."
                    )
                )
