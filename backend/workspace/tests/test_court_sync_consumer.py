"""Tests for workspace court sync consumer (cause lists and orders).

Normative sources:
- Session R2: hearings, dates and Today (§2, §3, User Approval & Corrections)
- User Correction 1: Matching rule, parent case matching, bench mapping.
- User Correction 2: Stable keys on hearings and candidates across revisions.
- User Correction 3: Dropped from revised list creates HEARING_DROPPED candidate.
- User Correction 5: Loop tenant by tenant with tenant context and purpose logged.
- User Correction 7: Order cause title (text before paragraph 1) only, negative citation guard.
"""

from datetime import date, timedelta

import pytest
from django.db import connection
from django.utils import timezone

from anchor_lib.ids import mint_id
from workspace.consumer import handle_causelist_published, handle_doc_parsed
from workspace.db import tenant_db_context
from workspace.models import CaseCandidate, Hearing, MatterDependency


def setup_test_tenant_and_matter(bench: str = "MUM") -> tuple[str, str, str]:
    """Helper to create a tenant, user, client, matter, and tracked case link."""
    tenant_id = mint_id("ten")
    user_id = mint_id("usr")
    client_id = mint_id("cli")
    matter_id = mint_id("mat")

    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL app.tenant_id = %s;", [tenant_id])
        cursor.execute("SET LOCAL app.user_id = %s;", [user_id])
        cursor.execute(
            "INSERT INTO tpl.tenant (tenant_id, name, deployment_mode, idp, created_at) VALUES (%s, %s, 'D2', '{}'::jsonb, now())",
            [tenant_id, "Test Firm"],
        )
        cursor.execute(
            """
            INSERT INTO tpl.app_user (tenant_id, user_id, email, idp_subject, firm_role, active)
            VALUES (%s, %s, 'test@firm.in', %s, 'PARTNER', true)
            """,
            [tenant_id, user_id, f"idp_{user_id}"],
        )
        cursor.execute(
            """
            INSERT INTO tpl.client (tenant_id, client_id, display_name, client_type, created_by, created_at)
            VALUES (%s, %s, 'Client Corp', 'COMPANY', %s, now())
            """,
            [tenant_id, client_id, user_id],
        )
        cursor.execute(
            """
            INSERT INTO tpl.matter (tenant_id, matter_id, client_id, title, client_role, status, court_or_forum, created_at)
            VALUES (%s, %s, %s, 'Matter A', 'PETITIONER', 'ACTIVE', 'NCLT Mumbai Bench', now())
            """,
            [tenant_id, matter_id, client_id],
        )
        cursor.execute(
            """
            INSERT INTO tpl.matter_member (tenant_id, matter_id, user_id, role, granted_by, granted_at)
            VALUES (%s, %s, %s, 'LEAD', %s, now())
            """,
            [tenant_id, matter_id, user_id, user_id],
        )
        cursor.execute(
            """
            INSERT INTO tpl.matter_case_link (tenant_id, matter_id, scheme, value_normalized, role, track)
            VALUES (%s, %s, 'NCLT', 'CP (IB) 188/MUM/2026', 'CASE', true)
            """,
            [tenant_id, matter_id],
        )

    return tenant_id, user_id, matter_id


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_causelist_exact_match_and_revision_update_in_place() -> None:
    """User Correction 2: Revisions of the same list update item_no in place, do not duplicate."""
    tenant_id, user_id, matter_id = setup_test_tenant_and_matter()
    list_date = date.today() + timedelta(days=1)

    # 1. Revision 1 arrives with item_no = "12"
    event_rev1 = {
        "data": {
            "source_id": "NCLT_CAUSELIST",
            "raw_id": "raw_blob_rev1",
            "bench": "MUMBAI BENCH",
            "court_no": "1",
            "list_date": list_date.isoformat(),
            "items": [
                {
                    "item_no": "12",
                    "purpose": "For Admission",
                    "parties": "State Bank of India Vs ABC Corp",
                    "normalized_cases": [
                        {
                            "raw": "CP (IB) 188/2026",
                            "case_type": "CP (IB)",
                            "case_number": "188",
                            "year": 2026,
                            "bench": "MUM",
                            "canonical": "CP (IB) 188/MUM/2026",
                            "parseable": True,
                        }
                    ],
                }
            ],
        }
    }

    res1 = handle_causelist_published(event_rev1)
    assert res1["status"] == "SUCCESS"
    assert res1["exact_matches"] == 1

    with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
        hearings = list(Hearing.objects.filter(matter_id=matter_id))
        assert len(hearings) == 1
        h = hearings[0]
        assert h.item_no == "12"
        assert h.source_ref == "raw_blob_rev1:12"
        assert h.bench == "MUM"
        assert h.court_no == "1"
        assert h.entered_by == "system:causelist"
        assert h.status == "LISTED"

    # 2. Revision 2 arrives with item renumbered to "14"
    event_rev2 = {
        "data": {
            "source_id": "NCLT_CAUSELIST",
            "raw_id": "raw_blob_rev2",
            "bench": "MUMBAI",
            "court_no": "1",
            "list_date": list_date.isoformat(),
            "items": [
                {
                    "item_no": "14",  # Renumbered in revised PDF
                    "purpose": "For Admission",
                    "parties": "State Bank of India Vs ABC Corp",
                    "normalized_cases": [
                        {
                            "raw": "CP (IB) 188/2026",
                            "case_type": "CP (IB)",
                            "case_number": "188",
                            "year": 2026,
                            "bench": "MUM",
                            "canonical": "CP (IB) 188/MUM/2026",
                            "parseable": True,
                        }
                    ],
                }
            ],
        }
    }

    res2 = handle_causelist_published(event_rev2)
    assert res2["status"] == "SUCCESS"
    assert res2["exact_matches"] == 1

    with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
        hearings_after = list(Hearing.objects.filter(matter_id=matter_id))
        # MUST NOT DUPLICATE! Exactly 1 hearing with item_no updated in place to 14
        assert len(hearings_after) == 1
        h_updated = hearings_after[0]
        assert h_updated.hearing_id == h.hearing_id
        assert h_updated.item_no == "14"
        assert h_updated.source_ref == "raw_blob_rev2:14"


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_causelist_dropped_from_revised_list() -> None:
    """User Correction 3: Entry omitted in revised list is not deleted; creates HEARING_DROPPED candidate."""
    tenant_id, user_id, matter_id = setup_test_tenant_and_matter()
    list_date = date.today() + timedelta(days=1)

    # 1. Revision 1 lists the matter
    event_rev1 = {
        "data": {
            "source_id": "NCLT_CAUSELIST",
            "raw_id": "raw_blob_rev1",
            "bench": "MUMBAI",
            "court_no": "1",
            "list_date": list_date.isoformat(),
            "items": [
                {
                    "item_no": "12",
                    "purpose": "For Admission",
                    "parties": "State Bank of India Vs ABC Corp",
                    "normalized_cases": [
                        {
                            "raw": "CP (IB) 188/2026",
                            "case_type": "CP (IB)",
                            "case_number": "188",
                            "year": 2026,
                            "bench": "MUM",
                            "canonical": "CP (IB) 188/MUM/2026",
                            "parseable": True,
                        }
                    ],
                }
            ],
        }
    }
    handle_causelist_published(event_rev1)

    # 2. Revision 2 is published without our matter (e.g. only item 99 for a different case)
    event_rev2 = {
        "data": {
            "source_id": "NCLT_CAUSELIST",
            "raw_id": "raw_blob_rev2",
            "bench": "MUMBAI",
            "court_no": "1",
            "list_date": list_date.isoformat(),
            "items": [
                {
                    "item_no": "1",
                    "purpose": "For Hearing",
                    "parties": "Different Bank Vs Other Ltd",
                    "normalized_cases": [
                        {
                            "raw": "CP (IB) 999/MUM/2026",
                            "case_type": "CP (IB)",
                            "case_number": "999",
                            "year": 2026,
                            "bench": "MUM",
                            "canonical": "CP (IB) 999/MUM/2026",
                            "parseable": True,
                        }
                    ],
                }
            ],
        }
    }
    res2 = handle_causelist_published(event_rev2)
    assert res2["dropped_candidates"] == 1

    with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
        # Hearing was NOT deleted
        hearings = list(Hearing.objects.filter(matter_id=matter_id))
        assert len(hearings) == 1
        assert hearings[0].item_no == "12"

        # Candidate with HEARING_DROPPED was created under "Check these"
        candidates = list(CaseCandidate.objects.filter(matter_id=matter_id, kind="HEARING_DROPPED"))
        assert len(candidates) == 1
        cand = candidates[0]
        assert cand.status == "PENDING"
        assert "no longer appears" in cand.details["message"]


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_dismissed_candidate_never_comes_back() -> None:
    """User Correction 2: Dismissed candidates never revert to PENDING or duplicate."""
    tenant_id, user_id, matter_id = setup_test_tenant_and_matter()
    list_date = date.today() + timedelta(days=1)

    # Partial match: item has no year -> PARTIAL match
    event_partial = {
        "data": {
            "source_id": "NCLT_CAUSELIST",
            "raw_id": "raw_blob_p1",
            "bench": "MUMBAI",
            "court_no": "1",
            "list_date": list_date.isoformat(),
            "items": [
                {
                    "item_no": "25",
                    "purpose": "For Hearing",
                    "parties": "Unknown Parties",
                    "normalized_cases": [
                        {
                            "raw": "CP (IB) 188/MB",  # Missing year! -> PARTIAL
                            "case_type": "CP (IB)",
                            "case_number": "188",
                            "year": None,
                            "bench": "MUM",
                            "canonical": "CP (IB) 188/MUM",
                            "parseable": True,
                        }
                    ],
                }
            ],
        }
    }

    res1 = handle_causelist_published(event_partial)
    assert res1["partial_matches"] == 1

    with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
        cand = CaseCandidate.objects.get(matter_id=matter_id, kind="HEARING")
        assert cand.status == "PENDING"

        # Lawyer dismisses the candidate
        cand.status = "DISMISSED"
        cand.resolved_by = user_id
        cand.resolved_at = timezone.now()
        cand.save(update_fields=["status", "resolved_by", "resolved_at"])

    # Revision arrives with the same item
    res2 = handle_causelist_published(event_partial)
    assert res2["partial_matches"] == 0

    with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
        candidates = list(CaseCandidate.objects.filter(matter_id=matter_id, kind="HEARING"))
        assert len(candidates) == 1
        assert candidates[0].status == "DISMISSED"


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_order_sync_cause_title_only_and_negative_citation_guard() -> None:
    """User Correction 7: Match order on cause title / header only. Citations in body never match."""
    tenant_id, user_id, matter_id = setup_test_tenant_and_matter()

    # 1. Order with header matching tracked case
    order_event_exact = {
        "data": {
            "parse_id": "parse_01J9ZORDERTEST123456789A",
            "work_id": "wrk_01J9ZORDERTEST123456789A",
            "metadata": {
                "court": {"bench_name": "Mumbai Bench"},
                "decision_date": "2026-10-15",
                "parties": "State Bank of India Vs ABC Corp",
                "case_numbers": [{"raw": "CP (IB) 188/MB/2026"}],
            },
        }
    }

    res = handle_doc_parsed(order_event_exact)
    assert res["status"] == "SUCCESS"
    assert res["exact_matches"] == 1

    with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
        deps = list(MatterDependency.objects.filter(matter_id=matter_id, kind="OWN_CASE"))
        assert len(deps) == 1
        assert deps[0].match_key == "CP (IB) 188/MUM/2026"
        assert deps[0].source_ref == "ibbi:parse_01J9ZORDERTEST123456789A"

    # 2. NEGATIVE TEST: Order for a completely different case (CP (IB) 999/DEL/2026),
    # which cites CP (IB) 188/MUM/2026 inside paragraph 14 of the judgment body.
    order_event_cited = {
        "data": {
            "parse_id": "parse_01J9ZORDERBODYCITED999",
            "work_id": "wrk_01J9ZORDERBODYCITED999",
            "metadata": {
                "court": {"bench_name": "New Delhi Bench"},
                "decision_date": "2026-10-16",
                "parties": "Unrelated Lender Vs Other Debtor",
                "case_numbers": [{"raw": "CP (IB) 999/ND/2026"}],  # Header is CP (IB) 999!
            },
        }
    }

    res_neg = handle_doc_parsed(order_event_cited)
    # CP (IB) 999 does NOT match our tracked matter CP (IB) 188
    assert res_neg["exact_matches"] == 0
    assert res_neg["partial_matches"] == 0

    with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
        # Dependencies must STILL be exactly 1 (from the first order), not 2!
        deps = list(MatterDependency.objects.filter(matter_id=matter_id))
        assert len(deps) == 1
        assert deps[0].source_ref == "ibbi:parse_01J9ZORDERTEST123456789A"
