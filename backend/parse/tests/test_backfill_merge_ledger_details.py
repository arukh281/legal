"""Tests for backfill_merge_ledger_details management command."""

from __future__ import annotations

import io
from datetime import UTC, datetime
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from anchor_lib.ids import mint_id
from parse.models import IdentityMergeLedger


@pytest.mark.django_db
def test_backfill_aborts_when_count_is_not_346() -> None:
    """Command must abort with CommandError when target row count != 346."""
    with pytest.raises(CommandError, match="Target row count mismatch: expected exactly 346 rows"):
        call_command("backfill_merge_ledger_details")


@pytest.mark.django_db
def test_backfill_dry_run_and_commit() -> None:
    """Command processes exactly 346 rows from s05b report: dry-run rolls back, commit updates."""
    report_path = Path("../eval/reports/s05b_orphan_works_report.txt")
    if not report_path.exists():
        report_path = Path("eval/reports/s05b_orphan_works_report.txt")
    assert report_path.exists()

    report_inventory: dict[str, str] = {}
    for line in report_path.read_text().splitlines():
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 6 and parts[2].startswith("wrk_"):
                report_inventory[parts[2]] = parts[5]

    assert len(report_inventory) == 346

    # Create 346 IdentityMergeLedger rows matching the report
    now = datetime.now(UTC)
    for dup_id in report_inventory:
        IdentityMergeLedger.objects.create(
            event_id=mint_id("evr"),
            kind="WORK",
            op="MERGE",
            from_id=dup_id,
            to_id=mint_id("wrk"),
            reason="REPARSE_DUPLICATE_RAW_BLOB",
            confidence=1.0,
            recorded_at=now,
            details=None,
        )

    # 1. Test Dry Run (default)
    out_dry = io.StringIO()
    call_command("backfill_merge_ledger_details", stdout=out_dry)
    dry_output = out_dry.getvalue()
    assert "ACTIVE: 294" in dry_output
    assert "PROVISIONAL: 52" in dry_output
    assert "[DRY RUN] Rolled back 346 details backfill updates cleanly." in dry_output

    # Verify rows were NOT modified
    assert IdentityMergeLedger.objects.filter(details__isnull=True).count() == 346

    # 2. Test Real Run (--commit)
    out_commit = io.StringIO()
    call_command("backfill_merge_ledger_details", commit=True, stdout=out_commit)
    commit_output = out_commit.getvalue()
    assert "Successfully backfilled details on 346 IdentityMergeLedger rows." in commit_output

    # Verify rows were modified with exact prior_status
    assert IdentityMergeLedger.objects.filter(details__isnull=True).count() == 0
    active_count = 0
    prov_count = 0
    for ledger in IdentityMergeLedger.objects.all():
        assert ledger.details is not None
        assert ledger.details["superseded_alias_ids"] == []
        assert ledger.details["retargeted_alias_ids"] == []
        assert ledger.details["repointed_mention_ids"] == []
        status = ledger.details["prior_status"]
        assert status == report_inventory[ledger.from_id]
        if status == "ACTIVE":
            active_count += 1
        elif status == "PROVISIONAL":
            prov_count += 1

    assert active_count == 294
    assert prov_count == 52
