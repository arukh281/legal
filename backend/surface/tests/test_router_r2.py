"""Tests for Surface REST API: Session R2 (Hearings, Dates, Candidates, Today, and Calendar).

Normative sources:
- Session R2: hearings, dates and Today
- docs/mvp/00_mvp_spec.md §4.1, §4.3
- docs/mvp/03_data_model_and_contracts.md §3.9, §3.10
- Non-negotiable 2: Rule-computed deadlines rejected until R4.
- Correction 6: Calendar file uses RFC 5545 all-day VALUE=DATE events.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client
from django.utils import timezone

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from workspace.models import AppUser, CaseCandidate, Hearing, MatterDependency, Tenant

IST = ZoneInfo("Asia/Kolkata")

pytestmark = pytest.mark.django_db(databases="__all__", transaction=True)


@pytest.fixture(autouse=True)
def enable_dev_auth(settings: Any) -> None:
    settings.DEBUG = True
    settings.DEV_AUTH_ENABLED = True


@pytest.fixture
def r2_setup() -> dict[str, Any]:
    t1 = mint_id("ten")
    u_lead = mint_id("usr")
    lead_email = f"lead_{u_lead}@firm1.in"

    with admin_db_context():
        Tenant.objects.create(
            tenant_id=t1,
            name="Firm 1",
            deployment_mode="D2",
            residency_policy="ANY",
            idp={"kind": "GOOGLE"},
        )
        AppUser.objects.create(
            tenant_id=t1,
            user_id=u_lead,
            email=lead_email,
            idp_subject=f"sub_{u_lead}",
            firm_role="PARTNER",
            active=True,
        )

    client = Client()
    # Authenticate lead user
    login_resp = client.post(
        "/api/auth/dev-login",
        data=json.dumps({"email": lead_email}),
        content_type="application/json",
    )
    assert login_resp.status_code == 200

    # Create client
    c_resp = client.post(
        "/api/clients",
        data=json.dumps({"display_name": "Tata Steel"}),
        content_type="application/json",
    )
    assert c_resp.status_code == 200
    client_id = c_resp.json()["client_id"]

    # Create matter
    m_resp = client.post(
        "/api/matters",
        data=json.dumps(
            {
                "client_id": client_id,
                "title": "Insolvency Petition Matter",
                "client_role": "FINANCIAL_CREDITOR",
                "case_type": "CP (IB)",
                "court_or_forum": "NCLT Mumbai Bench",
            }
        ),
        content_type="application/json",
    )
    assert m_resp.status_code == 200
    matter_id = m_resp.json()["matter_id"]

    return {
        "tenant_id": t1,
        "user_id": u_lead,
        "email": lead_email,
        "client": client,
        "client_id": client_id,
        "matter_id": matter_id,
    }


def test_manual_hearing_crud_and_outcome(r2_setup: dict[str, Any]) -> None:
    client = r2_setup["client"]
    matter_id = r2_setup["matter_id"]

    # 1. Create a manual hearing
    h_create_resp = client.post(
        f"/api/matters/{matter_id}/hearings",
        data=json.dumps(
            {
                "date": "2026-10-25",
                "court_no": "1",
                "item_no": "12",
                "purpose": "First listing for admission",
            }
        ),
        content_type="application/json",
    )
    assert h_create_resp.status_code == 200
    h_data = h_create_resp.json()
    assert h_data["hearing_id"].startswith("hrg_")
    assert h_data["source"] == "MANUAL"
    assert h_data["court_no"] == "1"
    assert h_data["item_no"] == "12"
    assert h_data["court_or_forum"] == "NCLT Mumbai Bench"

    hearing_id = h_data["hearing_id"]

    # 2. List hearings
    list_resp = client.get(f"/api/matters/{matter_id}/hearings")
    assert list_resp.status_code == 200
    hearings = list_resp.json()
    assert len(hearings) == 1
    assert hearings[0]["hearing_id"] == hearing_id

    # 3. Record outcome and schedule next date in one action
    outcome_resp = client.post(
        f"/api/hearings/{hearing_id}/outcome",
        data=json.dumps(
            {
                "outcome": "Notice issued; reply in two weeks",
                "status": "HEARD",
                "next_date": "2026-11-10",
                "next_purpose": "For filing reply and arguments",
            }
        ),
        content_type="application/json",
    )
    assert outcome_resp.status_code == 200
    updated_h = outcome_resp.json()
    assert updated_h["status"] == "HEARD"
    assert updated_h["outcome"] == "Notice issued; reply in two weeks"

    # Verify that the next hearing was automatically scheduled
    list_after = client.get(f"/api/matters/{matter_id}/hearings")
    assert list_after.status_code == 200
    all_h = list_after.json()
    assert len(all_h) == 2
    dates = [h["date"] for h in all_h]
    assert "2026-10-25" in dates
    assert "2026-11-10" in dates


def test_deadline_rule_id_rejection_and_manual_create(r2_setup: dict[str, Any]) -> None:
    client = r2_setup["client"]
    matter_id = r2_setup["matter_id"]

    # 1. Non-negotiable 2 check: rule_id must be refused before R4
    rejected_resp = client.post(
        f"/api/matters/{matter_id}/deadlines",
        data=json.dumps(
            {
                "label": "Reply to s.7 Petition",
                "due_on": "2026-11-05",
                "rule_id": "IBC-SEC7-REPLY",
            }
        ),
        content_type="application/json",
    )
    assert rejected_resp.status_code == 400
    assert "Rule-computed deadlines are disabled until Session R4" in rejected_resp.json()["detail"]

    # 2. Manual deadline creation
    create_resp = client.post(
        f"/api/matters/{matter_id}/deadlines",
        data=json.dumps(
            {
                "label": "File Counter-Affidavit",
                "due_on": "2026-11-08",
                "owner": "Adv. Sharma",
            }
        ),
        content_type="application/json",
    )
    assert create_resp.status_code == 200
    d_data = create_resp.json()
    assert d_data["deadline_id"].startswith("ddl_")
    assert d_data["rule_id"] is None
    assert d_data["kind"] == "MANUAL"
    assert d_data["source_note"] == "entered by Adv. Sharma, not computed"
    assert d_data["lifecycle"] == "CONFIRMED"

    deadline_id = d_data["deadline_id"]

    # 3. List deadlines
    list_resp = client.get(f"/api/matters/{matter_id}/deadlines")
    assert list_resp.status_code == 200
    deadlines = list_resp.json()
    assert len(deadlines) == 1
    assert deadlines[0]["deadline_id"] == deadline_id

    # 4. Lifecycle transition
    lifecycle_resp = client.post(
        f"/api/deadlines/{deadline_id}/lifecycle",
        data=json.dumps({"lifecycle": "DONE"}),
        content_type="application/json",
    )
    assert lifecycle_resp.status_code == 200
    assert lifecycle_resp.json()["lifecycle"] == "DONE"


def test_candidates_confirm_and_dismiss(r2_setup: dict[str, Any]) -> None:
    client = r2_setup["client"]
    matter_id = r2_setup["matter_id"]
    tenant_id = r2_setup["tenant_id"]

    # Create two candidates directly
    cnd1_id = mint_id("cnd")
    cnd2_id = mint_id("cnd")

    with admin_db_context():
        CaseCandidate.objects.create(
            tenant_id=tenant_id,
            candidate_id=cnd1_id,
            matter_id=matter_id,
            kind="HEARING",
            source="CAUSE_LIST",
            source_ref="https://nclt.gov.in/list1.pdf",
            case_number_raw="CP (IB) 188/2026",
            list_date=date(2026, 10, 28),
            bench="MUM",
            normalized_case_no="CP (IB) 188/2026",
            details={"court_no": "2", "item_no": "5", "purpose": "Directions"},
            status="PENDING",
        )
        CaseCandidate.objects.create(
            tenant_id=tenant_id,
            candidate_id=cnd2_id,
            matter_id=matter_id,
            kind="HEARING",
            source="CAUSE_LIST",
            source_ref="https://nclt.gov.in/list2.pdf",
            case_number_raw="CP (IB) 999/2026",
            list_date=date(2026, 10, 29),
            bench="DEL",
            normalized_case_no="CP (IB) 999/2026",
            details={"court_no": "1", "item_no": "14"},
            status="PENDING",
        )

    # 1. List pending candidates
    c_list_resp = client.get("/api/candidates")
    assert c_list_resp.status_code == 200
    c_items = c_list_resp.json()
    assert len(c_items) == 2

    # 2. Confirm candidate 1
    confirm_resp = client.post(f"/api/candidates/{cnd1_id}/confirm")
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["resolved"] == "CONFIRMED"

    # Confirming a hearing candidate creates a Hearing row
    with admin_db_context():
        hrg = Hearing.objects.filter(
            tenant_id=tenant_id, matter_id=matter_id, source="CAUSE_LIST"
        ).first()
        assert hrg is not None
        assert hrg.item_no == "5"

    # 3. Dismiss candidate 2
    dismiss_resp = client.post(f"/api/candidates/{cnd2_id}/dismiss")
    assert dismiss_resp.status_code == 200
    assert dismiss_resp.json()["resolved"] == "DISMISSED"

    # 4. Check that pending candidates list is now empty
    c_list_after = client.get("/api/candidates")
    assert c_list_after.status_code == 200
    assert len(c_list_after.json()) == 0


def test_today_dashboard_and_timeline(r2_setup: dict[str, Any]) -> None:
    client = r2_setup["client"]
    matter_id = r2_setup["matter_id"]
    tenant_id = r2_setup["tenant_id"]

    now_ist = timezone.now().astimezone(IST)
    today_d = now_ist.date()
    tomorrow_d = today_d + timedelta(days=1)

    # Insert a hearing today and a hearing tomorrow
    with admin_db_context():
        Hearing.objects.create(
            tenant_id=tenant_id,
            matter_id=matter_id,
            hearing_id=mint_id("hrg"),
            date=today_d,
            court_no="3",
            item_no="8",
            bench="NCLT Mumbai Bench",
            purpose="Admission hearing",
            source="MANUAL",
            status="LISTED",
            entered_by="user1",
        )
        Hearing.objects.create(
            tenant_id=tenant_id,
            matter_id=matter_id,
            hearing_id=mint_id("hrg"),
            date=tomorrow_d,
            court_no="1",
            item_no="2",
            bench="NCLT Mumbai Bench",
            purpose="For final orders",
            source="MANUAL",
            status="LISTED",
            entered_by="user1",
        )
        # Insert a public order dependency
        MatterDependency.objects.create(
            tenant_id=tenant_id,
            matter_id=matter_id,
            public_id="pdoc_ibbi_order_001",
            match_key="CP (IB) 188/2026",
            as_of_legal_date=today_d,
            kind="OWN_CASE",
            source_ref="https://ibbi.gov.in/orders/001.pdf",
        )

    # Call /today
    today_resp = client.get("/api/today")
    assert today_resp.status_code == 200
    t_data = today_resp.json()
    assert t_data["today_date"] == today_d.isoformat()
    assert len(t_data["today_hearings"]) == 1
    assert t_data["today_hearings"][0]["court_no"] == "3"
    assert len(t_data["tomorrow_hearings"]) == 1
    assert t_data["tomorrow_hearings"][0]["court_no"] == "1"
    assert len(t_data["recent_orders"]) == 1
    assert t_data["recent_orders"][0]["uncertified_badge"] is True

    # Call /matters/{id}/timeline
    timeline_resp = client.get(f"/api/matters/{matter_id}/timeline")
    assert timeline_resp.status_code == 200
    tl_items = timeline_resp.json()
    assert len(tl_items) >= 3
    # Check sorted descending by date
    dates = [item["date"] for item in tl_items]
    assert dates == sorted(dates, reverse=True)


def test_calendar_export_rfc5545(r2_setup: dict[str, Any]) -> None:
    client = r2_setup["client"]
    matter_id = r2_setup["matter_id"]
    tenant_id = r2_setup["tenant_id"]

    event_date = date(2026, 11, 15)

    with admin_db_context():
        Hearing.objects.create(
            tenant_id=tenant_id,
            matter_id=matter_id,
            hearing_id=mint_id("hrg"),
            date=event_date,
            court_no="2",
            item_no="10",
            bench="NCLT Mumbai Bench",
            purpose="Arguments on resolution plan",
            source="MANUAL",
            status="LISTED",
            entered_by="user1",
        )

    # 1. Matter calendar export
    m_cal_resp = client.get(f"/api/matters/{matter_id}/calendar/export")
    assert m_cal_resp.status_code == 200
    assert "text/calendar" in m_cal_resp["Content-Type"]
    assert f'filename="matter_{matter_id}_calendar.ics"' in m_cal_resp["Content-Disposition"]
    ics_text = m_cal_resp.content.decode("utf-8")

    # Correction 6: Must be RFC 5545 all-day VALUE=DATE
    assert "BEGIN:VCALENDAR" in ics_text
    assert "END:VCALENDAR" in ics_text
    assert "DTSTART;VALUE=DATE:20261115" in ics_text
    assert "DTEND;VALUE=DATE:20261116" in ics_text  # Next-day exclusive end date
    assert "SUMMARY:Hearing: Tata Steel - Insolvency Petition Matter" in ics_text or "SUMMARY:Hearing: Insolvency Petition Matter" in ics_text

    # 2. Firm-wide calendar export
    firm_cal_resp = client.get("/api/calendar/export")
    assert firm_cal_resp.status_code == 200
    assert "text/calendar" in firm_cal_resp["Content-Type"]
    assert 'filename="lawyer_brain_calendar.ics"' in firm_cal_resp["Content-Disposition"]
    firm_ics_text = firm_cal_resp.content.decode("utf-8")
    assert "DTSTART;VALUE=DATE:20261115" in firm_ics_text
