"""Contract tests for tpl.hearing, tpl.deadline, tpl.case_candidate, and tpl.matter_dependency."""

from datetime import date, timedelta

import pytest
from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from anchor_lib.ids import mint_id
from workspace.db import tenant_db_context
from workspace.models import (
    CaseCandidate,
    Deadline,
    Hearing,
)


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_deadline_rule_id_refusal_constraint() -> None:
    """Until R4 creates plc.rule_spec, refuse any insert with a non-null rule_id at DB level."""
    tenant_id = mint_id("ten")
    user_id = mint_id("usr")
    client_id = mint_id("cli")
    matter_id = mint_id("mat")
    deadline_id = mint_id("ddl")

    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL app.tenant_id = %s;", [tenant_id])
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
            VALUES (%s, %s, 'Client A', 'COMPANY', %s, now())
            """,
            [tenant_id, client_id, user_id],
        )
        cursor.execute(
            """
            INSERT INTO tpl.matter (tenant_id, matter_id, client_id, title, client_role, status, created_at)
            VALUES (%s, %s, %s, 'Matter A', 'PETITIONER', 'ACTIVE', now())
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

    # 1. Valid manual deadline insert succeeds
    with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
        d1 = Deadline.objects.create(
            tenant_id=tenant_id,
            matter_id=matter_id,
            deadline_id=deadline_id,
            rule_id=None,
            label="Reply as directed by the bench",
            kind="MANUAL",
            due_on=date.today() + timedelta(days=5),
            lifecycle="CONFIRMED",
            created_at=timezone.now(),
        )
        assert d1.deadline_id == deadline_id
        assert d1.rule_id is None

    # 2. Non-null rule_id MUST be refused by PostgreSQL check constraint
    invalid_deadline_id = mint_id("ddl")
    with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
        with transaction.atomic():
            with pytest.raises(IntegrityError) as exc_info:
                Deadline.objects.create(
                    tenant_id=tenant_id,
                    matter_id=matter_id,
                    deadline_id=invalid_deadline_id,
                    rule_id="prs_01M3Y2VR23YM6F6HTG56AK5XA1",  # Unverified / non-null rule_id!
                    label="Statutory Section 8 reply",
                    kind="MANUAL",
                    due_on=date.today() + timedelta(days=10),
                    lifecycle="CONFIRMED",
                    created_at=timezone.now(),
                )
        assert "chk_deadline_rule_id_refused" in str(exc_info.value).lower()


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_hearing_and_causelist_stable_key() -> None:
    """Correction 2: Key cause-list hearings by matter, date, bench, court_no."""
    tenant_id = mint_id("ten")
    user_id = mint_id("usr")
    client_id = mint_id("cli")
    matter_id = mint_id("mat")
    h1_id = mint_id("hrg")
    h2_id = mint_id("hrg")
    list_date = date.today() + timedelta(days=1)

    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL app.tenant_id = %s;", [tenant_id])
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
            VALUES (%s, %s, 'Client A', 'COMPANY', %s, now())
            """,
            [tenant_id, client_id, user_id],
        )
        cursor.execute(
            """
            INSERT INTO tpl.matter (tenant_id, matter_id, client_id, title, client_role, status, created_at)
            VALUES (%s, %s, %s, 'Matter A', 'PETITIONER', 'ACTIVE', now())
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

    with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
        # Insert initial cause-list hearing
        Hearing.objects.create(
            tenant_id=tenant_id,
            matter_id=matter_id,
            hearing_id=h1_id,
            date=list_date,
            court_no="1",
            item_no="12",
            bench="MUM",
            purpose="For Admission",
            source="CAUSE_LIST",
            source_ref="raw_blob_rev1:12",
            status="LISTED",
            entered_by="system:causelist",
            observed_at=timezone.now(),
        )

        # Duplicate cause-list hearing on same (matter, date, bench, court_no) raises IntegrityError
        with transaction.atomic():
            with pytest.raises(IntegrityError) as exc:
                Hearing.objects.create(
                    tenant_id=tenant_id,
                    matter_id=matter_id,
                    hearing_id=h2_id,
                    date=list_date,
                    court_no="1",
                    item_no="14",  # revised item number
                    bench="MUM",
                    purpose="For Admission",
                    source="CAUSE_LIST",
                    source_ref="raw_blob_rev2:14",
                    status="LISTED",
                    entered_by="system:causelist",
                    observed_at=timezone.now(),
                )
        assert "idx_hearing_causelist_stable" in str(exc.value)


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_case_candidate_stable_key() -> None:
    """Correction 2: Key candidates by matter, kind, list_date, bench, normalized_case_no."""
    tenant_id = mint_id("ten")
    user_id = mint_id("usr")
    client_id = mint_id("cli")
    matter_id = mint_id("mat")
    c1_id = mint_id("cnd")
    c2_id = mint_id("cnd")
    list_date = date.today() + timedelta(days=1)

    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL app.tenant_id = %s;", [tenant_id])
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
            VALUES (%s, %s, 'Client A', 'COMPANY', %s, now())
            """,
            [tenant_id, client_id, user_id],
        )
        cursor.execute(
            """
            INSERT INTO tpl.matter (tenant_id, matter_id, client_id, title, client_role, status, created_at)
            VALUES (%s, %s, %s, 'Matter A', 'PETITIONER', 'ACTIVE', now())
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

    with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
        CaseCandidate.objects.create(
            tenant_id=tenant_id,
            matter_id=matter_id,
            candidate_id=c1_id,
            kind="HEARING",
            source="CAUSE_LIST",
            source_ref="raw_rev1:10",
            case_number_raw="CP (IB) 123/2026",
            list_date=list_date,
            bench="MUM",
            normalized_case_no="CP (IB) 123/MUM/2026",
            details={"court_no": "2"},
            status="PENDING",
        )

        # Duplicate candidate on same (matter, kind, list_date, bench, normalized_case_no) is rejected
        with transaction.atomic():
            with pytest.raises(IntegrityError) as exc:
                CaseCandidate.objects.create(
                    tenant_id=tenant_id,
                    matter_id=matter_id,
                    candidate_id=c2_id,
                    kind="HEARING",
                    source="CAUSE_LIST",
                    source_ref="raw_rev2:15",  # different raw blob and item no
                    case_number_raw="CP (IB) 123/2026",
                    list_date=list_date,
                    bench="MUM",
                    normalized_case_no="CP (IB) 123/MUM/2026",
                    details={"court_no": "2"},
                    status="PENDING",
                )
        assert "uq_case_candidate_stable" in str(exc.value)
