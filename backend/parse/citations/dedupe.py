"""Deduplication and merge ledger engine for official vs aggregator order copies.

Normative sources:
- docs/mvp/01_corporate_corpus_and_sources.md §2.4 (IBBI copies vs official copies)
- docs/01_master_architecture.md §5.4, §6.3 (identity.merged.v1 / identity.split.v1)
- docs/mvp/03_data_model_and_contracts.md §3.3 (plc.identity_merge_ledger)
- S05b Directive #7:
  Auto-merge ONLY when court, normalised case number and decision date all match exactly.
  Ambiguous matches (same number, different year or bench) go to review queue with no merge.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from django.db import transaction

from anchor_lib.ids import mint_id
from ops.outbox import publish_event
from parse.models import (
    CitationMention,
    IdentifierAlias,
    IdentityMergeLedger,
    LegalCase,
    Work,
    WorkCase,
)


def _get_work_case_info(work: Work) -> list[tuple[str | None, str | None, int | None]]:
    """Return [(case_type, number, year)] for a work."""
    cases: list[LegalCase] = [
        wc.case for wc in WorkCase.objects.filter(work=work).select_related("case")
    ]
    return [(c.case_type, c.number, c.year) for c in cases if c]


def check_dedupe_match(work_a: Work, work_b: Work) -> tuple[bool, str, dict[str, Any]]:
    """Check if two works are exact duplicates or ambiguous.

    Returns (can_auto_merge, match_status, details).
    match_status in ("EXACT_MATCH", "AMBIGUOUS", "NO_MATCH").
    """
    # 1. Court match check
    if not work_a.court_id or not work_b.court_id:
        return False, "NO_MATCH", {"reason": "MISSING_COURT"}

    if work_a.court_id != work_b.court_id:
        # Check if one is a general court and other a specific bench (e.g. crt_IN_NCLT vs crt_IN_NCLT_MUM)
        if (
            work_a.court_id.startswith("crt_IN_NCLT")
            and work_b.court_id.startswith("crt_IN_NCLT")
            and work_a.court_id != work_b.court_id
        ):
            return False, "AMBIGUOUS", {"reason": "DIFFERENT_BENCH"}
        return False, "NO_MATCH", {"reason": "COURT_MISMATCH"}

    # 2. Decision date check
    if not work_a.decision_date or not work_b.decision_date:
        return False, "AMBIGUOUS", {"reason": "MISSING_DECISION_DATE"}

    if work_a.decision_date != work_b.decision_date:
        return False, "NO_MATCH", {"reason": "DATE_MISMATCH"}

    # 3. Case number check
    cases_a = _get_work_case_info(work_a)
    cases_b = _get_work_case_info(work_b)

    if not cases_a or not cases_b:
        return False, "AMBIGUOUS", {"reason": "MISSING_CASE_NUMBER"}

    # Compare case numbers
    for _ctype_a, num_a, yr_a in cases_a:
        for _ctype_b, num_b, yr_b in cases_b:
            if num_a and num_b:
                clean_a = num_a.strip().lower().replace(" ", "")
                clean_b = num_b.strip().lower().replace(" ", "")

                if clean_a == clean_b:
                    if yr_a == yr_b:
                        return (
                            True,
                            "EXACT_MATCH",
                            {
                                "court_id": work_a.court_id,
                                "decision_date": work_a.decision_date.isoformat(),
                                "case_number": num_a,
                                "year": yr_a,
                            },
                        )
                    else:
                        # Same number, different year -> AMBIGUOUS
                        return (
                            False,
                            "AMBIGUOUS",
                            {
                                "reason": "YEAR_MISMATCH",
                                "year_a": yr_a,
                                "year_b": yr_b,
                            },
                        )

    return False, "NO_MATCH", {"reason": "CASE_NUMBER_MISMATCH"}


def dedupe_and_merge(
    from_work_id: str,
    to_work_id: str,
    reason: str = "IBBI_OFFICIAL_DEDUPE",
) -> str:
    """Execute exact-match deduplication and merge from_work into to_work.

    Official copy wins for paragraph anchors. Records in identity_merge_ledger
    and emits identity.merged.v1 to ops.event_outbox.
    """
    now = datetime.now(UTC)

    with transaction.atomic():
        from_work = Work.objects.select_for_update().get(work_id=from_work_id)
        to_work = Work.objects.select_for_update().get(work_id=to_work_id)

        # Verify exact match
        can_merge, match_status, details = check_dedupe_match(from_work, to_work)
        if not can_merge:
            raise ValueError(
                f"Cannot auto-merge {from_work_id} into {to_work_id}: status={match_status}, details={details}"
            )

        # 1. Update from_work
        from_work.status = "MERGED"
        from_work.merged_into = to_work
        from_work.save(update_fields=["status", "merged_into"])

        # 2. Record in plc.identity_merge_ledger
        event_id = mint_id("evr")
        IdentityMergeLedger.objects.create(
            event_id=event_id,
            kind="WORK",
            op="MERGE",
            from_id=from_work_id,
            to_id=to_work_id,
            reason=reason,
            confidence=1.0,
            reversible_until=None,
            recorded_at=now,
        )

        # 3. Re-point active aliases
        IdentifierAlias.objects.filter(target_id=from_work_id, status="ACTIVE").update(
            status="SUPERSEDED"
        )

        # 4. Re-point citation mentions
        CitationMention.objects.filter(resolved_target_id=from_work_id).update(
            resolved_target_id=to_work_id
        )

        # 5. Emit plc.identity.merged.v1 outbox event
        publish_event(
            event_type="identity.merged.v1",
            source="p1/dedupe",
            subject=f"{from_work_id}->{to_work_id}",
            dataschema="schemareg://plc/identity.merged.v1/1.0",
            dataclass="PUBLIC",
            idempotencykey=f"merge|{event_id}",
            schemaversion="1.0",
            data={
                "kind": "WORK",
                "from_id": from_work_id,
                "to_id": to_work_id,
                "reason": reason,
                "confidence": 1.0,
            },
            topic="plc.identity.merged.v1",
            partition_key=from_work_id,
            tenantid=None,
        )

        return event_id


def split_work(merge_event_id: str, reason: str = "MERGE_REVERSAL") -> str:
    """Reverse a previous merge operation.

    Updates work status back to ACTIVE, records in identity_merge_ledger,
    and emits identity.split.v1 to ops.event_outbox.
    """
    now = datetime.now(UTC)

    with transaction.atomic():
        merge_entry = IdentityMergeLedger.objects.select_for_update().get(
            event_id=merge_event_id,
            op="MERGE",
        )
        from_work = Work.objects.select_for_update().get(work_id=merge_entry.from_id)

        # 1. Revert from_work
        from_work.status = "ACTIVE"
        from_work.merged_into = None
        from_work.save(update_fields=["status", "merged_into"])

        # 2. Record SPLIT in identity_merge_ledger
        split_event_id = mint_id("evr")
        IdentityMergeLedger.objects.create(
            event_id=split_event_id,
            kind="WORK",
            op="SPLIT",
            from_id=merge_entry.from_id,
            to_id=merge_entry.to_id,
            reason=reason,
            confidence=1.0,
            reversible_until=None,
            recorded_at=now,
        )

        # 3. Emit plc.identity.split.v1 event
        publish_event(
            event_type="identity.split.v1",
            source="p1/dedupe",
            subject=f"{merge_entry.from_id}->{merge_entry.to_id}",
            dataschema="schemareg://plc/identity.split.v1/1.0",
            dataclass="PUBLIC",
            idempotencykey=f"split|{split_event_id}",
            schemaversion="1.0",
            data={
                "kind": "WORK",
                "from_id": merge_entry.from_id,
                "to_id": merge_entry.to_id,
                "reason": reason,
                "confidence": 1.0,
            },
            topic="plc.identity.split.v1",
            partition_key=merge_entry.from_id,
            tenantid=None,
        )

        return split_event_id
