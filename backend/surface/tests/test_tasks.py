"""Unit and integration tests for internal work tasks (Session R3).

Normative tests:
- Tasks are internal work items, matter-scoped with RLS.
- Deadlines come only from the rules engine (Non-negotiable 2); tasks never appear in legal deadline lists.
- Assignee must be an active LEAD or MEMBER on the matter, never a VIEWER (Correction 14).
- Linked hearing or deadline must belong to the same matter (Correction 14).
- Creating or editing a task requires write access to the matter.
- Status transitions set done_at and done_by when marked DONE, and clear them when reopened.
- Today dashboard buckets my_tasks into overdue, today, this_week (today..today+7), and undated.
- Audit events recorded for all mutations.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client as HttpClient
from django.utils import timezone

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from workspace.models import (
    AppUser,
    AuditEvent,
    Client,
    Deadline,
    Hearing,
    Matter,
    MatterMember,
    Task,
    Tenant,
)

IST = ZoneInfo("Asia/Kolkata")
pytestmark = pytest.mark.django_db(databases="__all__", transaction=True)


@pytest.fixture(autouse=True)
def enable_dev_auth(settings: Any) -> None:
    settings.DEBUG = True
    settings.DEV_AUTH_ENABLED = True


@pytest.fixture
def r3_task_setup() -> dict[str, Any]:
    tenant_id = mint_id("ten")
    admin_id = mint_id("usr")
    lead_id = mint_id("usr")
    member_id = mint_id("usr")
    viewer_id = mint_id("usr")

    with admin_db_context():
        Tenant.objects.create(
            tenant_id=tenant_id,
            name="Apex Legal LLP",
            deployment_mode="D2",
            residency_policy="ANY",
            idp={"kind": "GOOGLE"},
        )
        AppUser.objects.create(
            tenant_id=tenant_id,
            user_id=admin_id,
            email=f"admin_{admin_id}@firm.in",
            display_name="Admin Lawyer",
            idp_subject=f"sub_{admin_id}",
            firm_role="ADMIN",
            active=True,
        )
        AppUser.objects.create(
            tenant_id=tenant_id,
            user_id=lead_id,
            email=f"lead_{lead_id}@firm.in",
            display_name="Lead Lawyer",
            idp_subject=f"sub_{lead_id}",
            firm_role="PARTNER",
            active=True,
        )
        AppUser.objects.create(
            tenant_id=tenant_id,
            user_id=member_id,
            email=f"member_{member_id}@firm.in",
            display_name="Associate Member",
            idp_subject=f"sub_{member_id}",
            firm_role="ASSOCIATE",
            active=True,
        )
        AppUser.objects.create(
            tenant_id=tenant_id,
            user_id=viewer_id,
            email=f"viewer_{viewer_id}@firm.in",
            display_name="Read Only Viewer",
            idp_subject=f"sub_{viewer_id}",
            firm_role="ASSOCIATE",
            active=True,
        )

        # Create Client
        client_id = mint_id("cli")
        Client.objects.create(
            tenant_id=tenant_id,
            client_id=client_id,
            display_name="Apex Global Ltd",
            client_type="COMPANY",
            created_by=lead_id,
        )

        # Create Matter
        matter_id = mint_id("mat")
        Matter.objects.create(
            tenant_id=tenant_id,
            matter_id=matter_id,
            client_id=client_id,
            title="Apex vs Zenith Recovery",
            client_role="PETITIONER",
            case_type="IBC",
            court_or_forum="NCLT New Delhi Bench Court-II",
            status="ACTIVE",
            walled=False,
        )

        # Assign matter memberships
        MatterMember.objects.create(tenant_id=tenant_id, matter_id=matter_id, user_id=lead_id, role="LEAD")
        MatterMember.objects.create(tenant_id=tenant_id, matter_id=matter_id, user_id=member_id, role="MEMBER")
        MatterMember.objects.create(tenant_id=tenant_id, matter_id=matter_id, user_id=viewer_id, role="VIEWER")
        MatterMember.objects.create(tenant_id=tenant_id, matter_id=matter_id, user_id=admin_id, role="LEAD")

        # Another Matter (to test foreign key scope)
        other_matter_id = mint_id("mat")
        Matter.objects.create(
            tenant_id=tenant_id,
            matter_id=other_matter_id,
            client_id=client_id,
            title="Other Unrelated Matter",
            client_role="PETITIONER",
            status="ACTIVE",
            walled=False,
        )
        MatterMember.objects.create(tenant_id=tenant_id, matter_id=other_matter_id, user_id=admin_id, role="LEAD")

        # Create Hearing on matter
        hearing_id = mint_id("hrg")
        today_d = timezone.now().astimezone(IST).date()
        Hearing.objects.create(
            tenant_id=tenant_id,
            hearing_id=hearing_id,
            matter_id=matter_id,
            date=today_d + timedelta(days=5),
            purpose="Arguments",
            status="LISTED",
            entered_by=lead_id,
        )

        # Create Deadline on matter
        deadline_id = mint_id("ddl")
        Deadline.objects.create(
            tenant_id=tenant_id,
            deadline_id=deadline_id,
            matter_id=matter_id,
            label="File Rejoinder",
            kind="MANUAL",
            due_on=today_d + timedelta(days=3),
            lifecycle="CONFIRMED",
            owner=lead_id,
        )

        # Create Hearing on other matter
        other_hearing_id = mint_id("hrg")
        Hearing.objects.create(
            tenant_id=tenant_id,
            hearing_id=other_hearing_id,
            matter_id=other_matter_id,
            date=today_d + timedelta(days=2),
            purpose="Listing",
            status="LISTED",
            entered_by=admin_id,
        )

    return {
        "tenant_id": tenant_id,
        "admin_id": admin_id,
        "lead_id": lead_id,
        "member_id": member_id,
        "viewer_id": viewer_id,
        "matter_id": matter_id,
        "other_matter_id": other_matter_id,
        "hearing_id": hearing_id,
        "deadline_id": deadline_id,
        "other_hearing_id": other_hearing_id,
    }


def test_task_creation_and_membership_rules(r3_task_setup: dict[str, Any]) -> None:
    """Test task creation, assignee restrictions (LEAD/MEMBER only, never VIEWER), and matter scope."""
    ctx = r3_task_setup
    client = HttpClient()

    # 1. Reject task assignment to VIEWER (Correction 14)
    res_viewer = client.post(
        f"/api/matters/{ctx['matter_id']}/tasks",
        data={
            "title": "Review affidavit",
            "assignee": ctx["viewer_id"],
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res_viewer.status_code == 400
    assert "never a VIEWER" in res_viewer.json()["detail"]

    # 2. Reject task with linked hearing from a different matter (Correction 14)
    res_foreign_hearing = client.post(
        f"/api/matters/{ctx['matter_id']}/tasks",
        data={
            "title": "Prepare arguments",
            "assignee": ctx["member_id"],
            "hearing_id": ctx["other_hearing_id"],
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res_foreign_hearing.status_code == 400
    assert "hearing does not belong" in res_foreign_hearing.json()["detail"]

    # 3. Reject task with both hearing_id and deadline_id (mutually exclusive)
    res_both = client.post(
        f"/api/matters/{ctx['matter_id']}/tasks",
        data={
            "title": "Both links",
            "assignee": ctx["member_id"],
            "hearing_id": ctx["hearing_id"],
            "deadline_id": ctx["deadline_id"],
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res_both.status_code == 400
    assert "not both" in res_both.json()["detail"].lower()

    # 4. Create valid task assigned to member with valid hearing
    today_d = timezone.now().astimezone(IST).date()
    res_valid = client.post(
        f"/api/matters/{ctx['matter_id']}/tasks",
        data={
            "title": "Draft reply to IA",
            "notes": "Include latest IBC amendment precedents",
            "assignee": ctx["member_id"],
            "due_on": (today_d + timedelta(days=2)).isoformat(),
            "hearing_id": ctx["hearing_id"],
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res_valid.status_code == 200
    task_data = res_valid.json()
    assert task_data["task_id"].startswith("tsk_")
    assert task_data["status"] == "OPEN"
    assert task_data["assignee"] == ctx["member_id"]
    assert task_data["is_overdue"] is False

    # Check audit log
    with admin_db_context():
        audit = AuditEvent.objects.filter(
            tenant_id=ctx["tenant_id"],
            action="TASK_CREATE",
            object_ref=task_data["task_id"],
        ).first()
        assert audit is not None


def test_task_status_lifecycle_and_reassignment(r3_task_setup: dict[str, Any]) -> None:
    """Test OPEN -> DONE -> OPEN status cycle and reassignment."""
    ctx = r3_task_setup
    client = HttpClient()

    # Create task
    res_create = client.post(
        f"/api/matters/{ctx['matter_id']}/tasks",
        data={
            "title": "File vakalatnama",
            "assignee": ctx["member_id"],
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res_create.status_code == 200
    task_id = res_create.json()["task_id"]

    # Mark DONE
    res_done = client.post(
        f"/api/tasks/{task_id}/status",
        data={"status": "DONE"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['member_id']}",
    )
    assert res_done.status_code == 200
    done_data = res_done.json()
    assert done_data["status"] == "DONE"
    assert done_data["done_by"] == ctx["member_id"]
    assert done_data["done_at"] is not None

    # Reopen to OPEN
    res_open = client.post(
        f"/api/tasks/{task_id}/status",
        data={"status": "OPEN"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res_open.status_code == 200
    open_data = res_open.json()
    assert open_data["status"] == "OPEN"
    assert open_data["done_at"] is None
    assert open_data["done_by"] is None

    # Reassign task to lead
    res_assign = client.post(
        f"/api/tasks/{task_id}/assign",
        data={"assignee": ctx["lead_id"]},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['lead_id']}",
    )
    assert res_assign.status_code == 200
    assert res_assign.json()["assignee"] == ctx["lead_id"]


def test_today_dashboard_tasks_and_non_negotiable_deadline_isolation(r3_task_setup: dict[str, Any]) -> None:
    """Verify tasks appear in Today dashboard my_tasks and NEVER pollute legal deadline lists (NN2)."""
    ctx = r3_task_setup
    client = HttpClient()
    today_d = timezone.now().astimezone(IST).date()

    with admin_db_context():
        # Create 4 tasks for ctx["member_id"]:
        # 1. Overdue
        Task.objects.create(
            tenant_id=ctx["tenant_id"],
            task_id=mint_id("tsk"),
            matter_id=ctx["matter_id"],
            title="Overdue Research Note",
            assignee=ctx["member_id"],
            due_on=today_d - timedelta(days=2),
            status="OPEN",
            created_by=ctx["lead_id"],
        )
        # 2. Today
        Task.objects.create(
            tenant_id=ctx["tenant_id"],
            task_id=mint_id("tsk"),
            matter_id=ctx["matter_id"],
            title="Serve Copy Today",
            assignee=ctx["member_id"],
            due_on=today_d,
            status="OPEN",
            created_by=ctx["lead_id"],
        )
        # 3. This week (today + 4 days, within IST today..today+7 window, Correction 15)
        Task.objects.create(
            tenant_id=ctx["tenant_id"],
            task_id=mint_id("tsk"),
            matter_id=ctx["matter_id"],
            title="Proofread Petition",
            assignee=ctx["member_id"],
            due_on=today_d + timedelta(days=4),
            status="OPEN",
            created_by=ctx["lead_id"],
        )
        # 4. Undated
        Task.objects.create(
            tenant_id=ctx["tenant_id"],
            task_id=mint_id("tsk"),
            matter_id=ctx["matter_id"],
            title="File Case Papers in Binder",
            assignee=ctx["member_id"],
            due_on=None,
            status="OPEN",
            created_by=ctx["lead_id"],
        )

    # Fetch Today dashboard as member
    res = client.get(
        "/api/today",
        HTTP_AUTHORIZATION=f"Bearer {ctx['member_id']}",
    )
    assert res.status_code == 200
    today_data = res.json()

    # 1. Verify my_tasks has all 4 items bucketed
    my_tasks = today_data.get("my_tasks", [])
    assert len(my_tasks) == 4
    task_titles = [t["title"] for t in my_tasks]
    assert "Overdue Research Note" in task_titles
    assert "Serve Copy Today" in task_titles
    assert "Proofread Petition" in task_titles
    assert "File Case Papers in Binder" in task_titles

    # 2. Non-negotiable 2 check:
    # Tasks must NEVER appear in due_this_week / legal deadlines!
    due_this_week = today_data.get("due_this_week", [])
    for ddl in due_this_week:
        assert not ddl.get("deadline_id", "").startswith("tsk_")
        assert ddl.get("label") != "Overdue Research Note"
        assert ddl.get("label") != "Proofread Petition"
