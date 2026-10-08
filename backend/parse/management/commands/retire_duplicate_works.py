"""Management command to retire duplicate works resulting from historical re-parses.

Normative sources:
- AGENTS.md §4 & §5 (Non-negotiables: bitemporal Assertion ledger, zero deletions)
- docs/mvp/03_data_model_and_contracts.md §3.3 (plc.identity_merge_ledger)
- docs/01_master_architecture.md §2.4 & §5.4 (identity dedupe and merge rules)
- Session S05b Blocker #2 / User Follow-up directive #4:
  - Atomic single transaction
  - Before and after counts
  - Zero deletions across all tables
  - Confirm no citation or STUB alias points at a duplicate work
  - Emit plc.identity.merged.v1 CloudEvents to ops.event_outbox
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from anchor_lib.ids import mint_id
from ingest.models import Capture
from ops.outbox import publish_event
from parse.models import (
    Anchor,
    CitationMention,
    IdentifierAlias,
    IdentityMergeLedger,
    Manifestation,
    ParseRun,
    Work,
)


class Command(BaseCommand):
    help = "Retire duplicate historical works into canonical works via identity_merge_ledger."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Simulate the retirement without committing database changes.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = options.get("dry_run", False)
        now = datetime.now(UTC)

        self.stdout.write(
            self.style.NOTICE("=== Starting Duplicate Works Retirement (Single Transaction) ===")
        )
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE: Changes will be rolled back."))

        # 1. Identify distinct raw_ids and their canonical vs duplicate works
        distinct_raw_ids = list(Capture.objects.values_list("raw_id", flat=True).distinct())

        canonical_by_raw: dict[str, str] = {}
        dupe_map: dict[str, str] = {}  # dup_work_id -> canonical_work_id

        for raw_id in distinct_raw_ids:
            runs = list(ParseRun.objects.filter(raw_ids__contains=[raw_id]).order_by("-created_at"))
            if not runs:
                continue
            canonical_work_id = runs[0].work_id
            canonical_by_raw[raw_id] = canonical_work_id
            for r in runs[1:]:
                if r.work_id != canonical_work_id and r.work_id not in dupe_map:
                    work = Work.objects.filter(work_id=r.work_id).first()
                    if work and work.status != "MERGED":
                        dupe_map[r.work_id] = canonical_work_id

        duplicate_count = len(dupe_map)
        canonical_count = len(set(canonical_by_raw.values()))

        self.stdout.write(f"Analyzed {len(distinct_raw_ids)} distinct captured raw PDFs.")
        self.stdout.write(f"Identified {canonical_count} canonical works.")
        self.stdout.write(f"Identified {duplicate_count} duplicate works to retire.")

        if duplicate_count == 0:
            self.stdout.write(self.style.SUCCESS("No duplicate works found. Nothing to retire."))
            return

        with transaction.atomic():
            canonical_ids = set(canonical_by_raw.values())
            duplicate_ids = set(dupe_map.keys())

            # 1. Assert inside transaction that no duplicate is also canonical for another raw_id
            overlap = duplicate_ids & canonical_ids
            assert not overlap, (
                f"Integrity violation: duplicate work(s) {overlap} cannot also be canonical for another raw_id! Aborting."
            )

            # 2. Assert inside transaction that no canonical work is MERGED
            merged_canonicals = list(
                Work.objects.filter(work_id__in=canonical_ids, status="MERGED").values_list(
                    "work_id", flat=True
                )
            )
            assert not merged_canonicals, (
                f"Integrity violation: canonical work(s) {merged_canonicals} are in MERGED status! Aborting."
            )

            # BEFORE AUDIT COUNTS
            before_work_total = Work.objects.count()
            before_work_active = Work.objects.filter(status="ACTIVE").count()
            before_work_provisional = Work.objects.filter(status="PROVISIONAL").count()
            before_work_stub = Work.objects.filter(status="STUB").count()
            before_work_merged = Work.objects.filter(status="MERGED").count()

            before_parserun_total = ParseRun.objects.count()
            before_anchor_total = Anchor.objects.count()
            before_manifestation_total = Manifestation.objects.count()
            before_merge_ledger_total = IdentityMergeLedger.objects.count()
            before_citation_total = CitationMention.objects.count()
            before_alias_total = IdentifierAlias.objects.count()

            dup_ids = list(dupe_map.keys())
            before_cites_on_dupes = CitationMention.objects.filter(
                resolved_target_id__in=dup_ids
            ).count()
            before_cites_with_citing_dupe = CitationMention.objects.filter(
                citing_work_id__in=dup_ids
            ).count()
            before_aliases_on_dupes = IdentifierAlias.objects.filter(
                target_id__in=dup_ids, status="ACTIVE"
            ).count()

            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("--- BEFORE RETIREMENT COUNTS ---")
            self.stdout.write("=" * 60)
            self.stdout.write(f"  Total Works:                     {before_work_total}")
            self.stdout.write(f"    • ACTIVE:                      {before_work_active}")
            self.stdout.write(f"    • PROVISIONAL:                 {before_work_provisional}")
            self.stdout.write(f"    • STUB:                        {before_work_stub}")
            self.stdout.write(f"    • MERGED:                      {before_work_merged}")
            self.stdout.write(f"  Total ParseRuns:                 {before_parserun_total}")
            self.stdout.write(f"  Total Anchors:                   {before_anchor_total}")
            self.stdout.write(f"  Total Manifestations:            {before_manifestation_total}")
            self.stdout.write(f"  Total Merge Ledger Rows:         {before_merge_ledger_total}")
            self.stdout.write(f"  Total Citation Mentions:         {before_citation_total}")
            self.stdout.write(f"  Total Identifier Aliases:        {before_alias_total}")
            self.stdout.write(f"  Citations Pointing to Dupes:     {before_cites_on_dupes}")
            self.stdout.write(f"  Citations with citing_work_id:   {before_cites_with_citing_dupe}")
            self.stdout.write(f"  Aliases Pointing to Dupes:       {before_aliases_on_dupes}")

            # RETIREMENT EXECUTION
            merges_performed = 0
            for dup_id, can_id in dupe_map.items():
                dup_work = Work.objects.select_for_update().get(work_id=dup_id)
                prior_status = dup_work.status
                record_reason = f"REPARSE_DUPLICATE_RAW_BLOB|prior_status={prior_status}"

                # 1. Update Work status to MERGED and set merged_into
                dup_work.status = "MERGED"
                dup_work.merged_into_id = can_id
                dup_work.save(update_fields=["status", "merged_into"])

                # 2. Re-point Manifestations to canonical work
                Manifestation.objects.filter(work_id=dup_id).update(work_id=can_id)

                # 3. Re-point CitationMentions if any
                CitationMention.objects.filter(resolved_target_id=dup_id).update(
                    resolved_target_id=can_id
                )

                # 4. Re-target ACTIVE aliases to canonical work (new ACTIVE alias on can_id + old SUPERSEDED on dup_id)
                event_id = mint_id("evr")
                active_aliases = list(
                    IdentifierAlias.objects.filter(target_id=dup_id, status="ACTIVE")
                )
                for alias in active_aliases:
                    alias.status = "SUPERSEDED"
                    alias.save(update_fields=["status"])

                    target_alias = IdentifierAlias.objects.filter(
                        scheme=alias.scheme,
                        value_normalized=alias.value_normalized,
                        target_id=can_id,
                    ).first()
                    if not target_alias:
                        IdentifierAlias.objects.create(
                            scheme=alias.scheme,
                            value_normalized=alias.value_normalized,
                            target_id=can_id,
                            confidence=alias.confidence,
                            source=alias.source,
                            trust_tier=alias.trust_tier,
                            status="ACTIVE",
                            first_seen=now,
                            evidence={
                                **alias.evidence,
                                "retargeted_from": dup_id,
                                "merge_event_id": event_id,
                            },
                        )
                    elif target_alias.status != "ACTIVE":
                        target_alias.status = "ACTIVE"
                        target_alias.save(update_fields=["status"])

                # 5. Insert audit row into plc.identity_merge_ledger with prior_status
                IdentityMergeLedger.objects.create(
                    event_id=event_id,
                    kind="WORK",
                    op="MERGE",
                    from_id=dup_id,
                    to_id=can_id,
                    reason=record_reason,
                    confidence=1.0,
                    reversible_until=None,
                    recorded_at=now,
                )

                # 6. Emit plc.identity.merged.v1 CloudEvent
                publish_event(
                    event_type="identity.merged.v1",
                    source="p1/dedupe",
                    subject=f"{dup_id}->{can_id}",
                    dataschema="schemareg://plc/identity.merged.v1/1.0",
                    dataclass="PUBLIC",
                    idempotencykey=f"merge|{event_id}",
                    schemaversion="1.0",
                    data={
                        "kind": "WORK",
                        "from_id": dup_id,
                        "to_id": can_id,
                        "reason": record_reason,
                        "confidence": 1.0,
                    },
                    topic="plc.identity.merged.v1",
                    partition_key=dup_id,
                    tenantid=None,
                )

                merges_performed += 1

            # AFTER AUDIT COUNTS
            after_work_total = Work.objects.count()
            after_work_active = Work.objects.filter(status="ACTIVE").count()
            after_work_provisional = Work.objects.filter(status="PROVISIONAL").count()
            after_work_stub = Work.objects.filter(status="STUB").count()
            after_work_merged = Work.objects.filter(status="MERGED").count()

            after_parserun_total = ParseRun.objects.count()
            after_anchor_total = Anchor.objects.count()
            after_manifestation_total = Manifestation.objects.count()
            after_merge_ledger_total = IdentityMergeLedger.objects.count()
            after_citation_total = CitationMention.objects.count()
            after_alias_total = IdentifierAlias.objects.count()

            after_cites_on_dupes = CitationMention.objects.filter(
                resolved_target_id__in=dup_ids
            ).count()
            after_cites_with_citing_dupe = CitationMention.objects.filter(
                citing_work_id__in=dup_ids
            ).count()
            after_aliases_on_dupes = IdentifierAlias.objects.filter(
                target_id__in=dup_ids, status="ACTIVE"
            ).count()

            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("--- AFTER RETIREMENT COUNTS ---")
            self.stdout.write("=" * 60)
            self.stdout.write(f"  Total Works:                     {after_work_total}")
            self.stdout.write(f"    • ACTIVE:                      {after_work_active}")
            self.stdout.write(f"    • PROVISIONAL:                 {after_work_provisional}")
            self.stdout.write(f"    • STUB:                        {after_work_stub}")
            self.stdout.write(f"    • MERGED:                      {after_work_merged}")
            self.stdout.write(f"  Total ParseRuns:                 {after_parserun_total}")
            self.stdout.write(f"  Total Anchors:                   {after_anchor_total}")
            self.stdout.write(f"  Total Manifestations:            {after_manifestation_total}")
            self.stdout.write(f"  Total Merge Ledger Rows:         {after_merge_ledger_total}")
            self.stdout.write(f"  Total Citation Mentions:         {after_citation_total}")
            self.stdout.write(f"  Total Identifier Aliases:        {after_alias_total}")
            self.stdout.write(f"  Citations Pointing to Dupes:     {after_cites_on_dupes}")
            self.stdout.write(f"  Citations with citing_work_id:   {after_cites_with_citing_dupe}")
            self.stdout.write(f"  Aliases Pointing to Dupes:       {after_aliases_on_dupes}")

            # ZERO DELETION & INTEGRITY ASSERTIONS
            assert after_work_total == before_work_total, (
                f"Work count changed: {before_work_total} -> {after_work_total}. Deletes forbidden!"
            )
            assert after_parserun_total == before_parserun_total, (
                "ParseRun count changed! Deletes forbidden!"
            )
            assert after_anchor_total == before_anchor_total, (
                "Anchor count changed! Deletes forbidden!"
            )
            assert after_manifestation_total == before_manifestation_total, (
                "Manifestation count changed! Deletes forbidden!"
            )
            assert after_merge_ledger_total == before_merge_ledger_total + merges_performed, (
                f"Merge ledger entries mismatch: expected +{merges_performed}"
            )
            assert after_cites_on_dupes == 0, (
                f"Found {after_cites_on_dupes} citations pointing to duplicate works!"
            )
            assert after_cites_with_citing_dupe == 0, (
                f"Found {after_cites_with_citing_dupe} citations with citing_work_id in duplicate works!"
            )
            assert after_aliases_on_dupes == 0, (
                f"Found {after_aliases_on_dupes} aliases pointing to duplicate works!"
            )

            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING(
                        f"\n[DRY RUN] Rolled back {merges_performed} retirement operations cleanly."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nSuccessfully retired {merges_performed} duplicate works into canonical works in a single atomic transaction."
                    )
                )
