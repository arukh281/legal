"""Management command: backfill_tombstone_forwards.

Idempotently inspects TOMBSTONED anchors with null forward_to and aligns them
to containing LIVE anchors within the same work using text containment and QuoteSelector.

Normative sources:
- Session S07 Close-Out Directive #1
- docs/mvp/03_data_model_and_contracts.md §3.4
- docs/01_master_architecture.md §5.5
"""

from __future__ import annotations

import logging
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from anchor_lib.selectors import QuoteSelector
from core.db_router import admin_db_context
from parse.models import Anchor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Idempotently backfills forward_to pointers on TOMBSTONED anchors."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--all",
            action="store_true",
            help="Re-evaluate all tombstoned anchors, not just those with null forward_to.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Inspect and report without committing database changes.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        re_evaluate_all: bool = bool(options.get("all", False))
        dry_run: bool = bool(options.get("dry_run", False))

        self.stdout.write("=" * 80)
        self.stdout.write("BACKFILL TOMBSTONE FORWARD POINTERS")
        self.stdout.write(f"[*] Re-evaluate all: {re_evaluate_all} | Dry-run: {dry_run}")
        self.stdout.write("=" * 80)

        with admin_db_context():
            if re_evaluate_all:
                qs = Anchor.objects.filter(state="TOMBSTONED").order_by("anchor_id")
            else:
                qs = Anchor.objects.filter(state="TOMBSTONED", forward_to__isnull=True).order_by("anchor_id")

            tombs = list(qs)
            total = len(tombs)
            self.stdout.write(f"[*] Inspecting {total} tombstoned anchor records...")

            mapped = 0
            already_mapped = 0
            unmappable = 0

            with transaction.atomic(using="owner"):
                for tomb in tombs:
                    if tomb.forward_to and not re_evaluate_all:
                        already_mapped += 1
                        continue

                    live_anchors = list(
                        Anchor.objects.filter(work_id=tomb.work_id, state="LIVE")
                    )
                    t_text = tomb.text.strip()
                    target: Anchor | None = None

                    # 1. Exact or stripped containment
                    if t_text:
                        for live in live_anchors:
                            if t_text in live.text:
                                target = live
                                break

                    # 2. QuoteSelector prefix/suffix match
                    if not target and t_text and (tomb.quote_prefix or tomb.quote_suffix):
                        qs_obj = QuoteSelector(
                            exact=t_text[:min(len(t_text), 100)],
                            prefix=tomb.quote_prefix or "",
                            suffix=tomb.quote_suffix or "",
                        )
                        for live in live_anchors:
                            if qs_obj.find_in(live.text) is not None:
                                target = live
                                break

                    if target:
                        if tomb.forward_to == target.anchor_id:
                            already_mapped += 1
                        else:
                            if not dry_run:
                                tomb.forward_to = target.anchor_id
                                tomb.save(update_fields=["forward_to"])
                            mapped += 1
                    else:
                        if tomb.forward_to:
                            already_mapped += 1
                        else:
                            unmappable += 1

                if dry_run:
                    transaction.set_rollback(True, using="owner")

            self.stdout.write("-" * 80)
            self.stdout.write("SUMMARY RESULTS:")
            self.stdout.write(f"  - Total tombstone records inspected: {total}")
            self.stdout.write(f"  - Newly mapped with forward_to:       {mapped}")
            self.stdout.write(f"  - Already mapped:                     {already_mapped}")
            self.stdout.write(f"  - Unmappable (forward_to remains null): {unmappable}")
            self.stdout.write("=" * 80)
