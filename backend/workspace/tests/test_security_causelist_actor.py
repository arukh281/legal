"""Security tests for migration 0007 and system:causelist background actor isolation.

Normative sources:
- Session R2: hearings, dates and Today (Mandate 3)
- docs/mvp/03_data_model_and_contracts.md §1:
  "app_rw reads plc and reads/writes tpl under RLS. worker has BYPASSRLS but must set app.purpose."
- R2 Security Mandate:
  "The system:causelist actor must only be usable by the worker DB role, only for writing
   tpl.hearing and tpl.case_candidate, never for reading documents, and never settable by an app request.
   Add tests: an app-role session that sets the actor gets nothing extra."
"""

from datetime import date

import pytest
from django.db import DatabaseError, connections

from anchor_lib.ids import mint_id


@pytest.fixture
def seeded_tenant_with_matter_and_doc() -> dict[str, str]:
    """Create a tenant with a matter, hearing, candidate, and private document in the vault."""
    tenant_id = mint_id("ten")
    user_id = mint_id("usr")
    client_id = mint_id("cli")
    matter_id = mint_id("mat")
    pdoc_id = mint_id("pdoc")
    hearing_id = mint_id("hrg")
    candidate_id = mint_id("cnd")

    with connections["admin"].cursor() as cursor:
        cursor.execute("SET LOCAL app.tenant_id = %s;", [tenant_id])
        cursor.execute("SET LOCAL app.user_id = %s;", [user_id])

        cursor.execute(
            "INSERT INTO tpl.tenant (tenant_id, name, deployment_mode, idp, created_at) VALUES (%s, %s, 'D2', '{}'::jsonb, now())",
            [tenant_id, "Sec Test Firm"],
        )
        cursor.execute(
            """
            INSERT INTO tpl.app_user (tenant_id, user_id, email, idp_subject, firm_role, active)
            VALUES (%s, %s, 'partner@sectest.in', %s, 'PARTNER', true)
            """,
            [tenant_id, user_id, f"idp_{user_id}"],
        )
        cursor.execute(
            """
            INSERT INTO tpl.client (tenant_id, client_id, display_name, client_type, created_by, created_at)
            VALUES (%s, %s, 'Secure Client', 'COMPANY', %s, now())
            """,
            [tenant_id, client_id, user_id],
        )
        cursor.execute(
            """
            INSERT INTO tpl.matter (tenant_id, matter_id, client_id, title, client_role, status, court_or_forum, created_at)
            VALUES (%s, %s, %s, 'Secure Matter', 'PETITIONER', 'ACTIVE', 'NCLT Mumbai Bench', now())
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
            VALUES (%s, %s, 'NCLT', 'CP (IB) 100/MUM/2026', 'CASE', true)
            """,
            [tenant_id, matter_id],
        )
        cursor.execute(
            """
            INSERT INTO tpl.pdoc (tenant_id, pdoc_id, matter_id, doc_type, provenance, trust_label, privilege_class, stage, title, created_by, created_at)
            VALUES (%s, %s, %s, 'PDF', 'UPLOAD', 'TENANT_CLIENT_DOC', 'ATTORNEY_CLIENT', 'PLEADING', 'Secret Doc', %s, now())
            """,
            [tenant_id, pdoc_id, matter_id, user_id],
        )
        cursor.execute(
            """
            INSERT INTO tpl.hearing (tenant_id, hearing_id, matter_id, date, bench, court_no, item_no, purpose, status, entered_by, observed_at)
            VALUES (%s, %s, %s, %s, 'MUM', '1', '5', 'Admission', 'LISTED', %s, now())
            """,
            [tenant_id, hearing_id, matter_id, date.today(), user_id],
        )
        cursor.execute(
            """
            INSERT INTO tpl.case_candidate (tenant_id, candidate_id, matter_id, kind, source, source_ref, case_number_raw, normalized_case_no, status, created_at)
            VALUES (%s, %s, %s, 'HEARING', 'CAUSE_LIST', 'ref_1', 'CP 100/2026', 'CP (IB) 100/MUM/2026', 'PENDING', now())
            """,
            [tenant_id, candidate_id, matter_id],
        )

    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "matter_id": matter_id,
        "pdoc_id": pdoc_id,
        "hearing_id": hearing_id,
        "candidate_id": candidate_id,
    }


@pytest.mark.django_db(transaction=True, databases=["default", "admin", "owner", "worker"])
def test_app_role_cannot_elevate_with_system_causelist_actor(
    seeded_tenant_with_matter_and_doc: dict[str, str],
) -> None:
    """An app-role (app_rw) session setting app.user_id = 'system:causelist' gets nothing extra."""
    info = seeded_tenant_with_matter_and_doc
    tenant_id = info["tenant_id"]
    matter_id = info["matter_id"]

    with connections["default"].cursor() as cursor:
        cursor.execute("SELECT SESSION_USER;")
        assert cursor.fetchone()[0] == "app_rw", "connections['default'] must run as app_rw"

        cursor.execute("SET LOCAL app.tenant_id = %s;", [tenant_id])
        # Attempt to spoof background actor
        cursor.execute("SET LOCAL app.user_id = 'system:causelist';")
        cursor.execute("SET LOCAL app.purpose = 'CAUSELIST_SYNC';")

        # 1. cannot read matter
        cursor.execute("SELECT count(*) FROM tpl.matter WHERE matter_id = %s;", [matter_id])
        assert cursor.fetchone()[0] == 0, "app_rw session must not read matters via system actor spoofing"

        # 2. cannot read hearings
        cursor.execute("SELECT count(*) FROM tpl.hearing WHERE matter_id = %s;", [matter_id])
        assert cursor.fetchone()[0] == 0, "app_rw session must not read hearings via system actor spoofing"

        # 3. cannot read candidates
        cursor.execute("SELECT count(*) FROM tpl.case_candidate WHERE matter_id = %s;", [matter_id])
        assert cursor.fetchone()[0] == 0, "app_rw session must not read candidates via system actor spoofing"

        # 4. cannot read document vault
        cursor.execute("SELECT count(*) FROM tpl.pdoc WHERE matter_id = %s;", [matter_id])
        assert cursor.fetchone()[0] == 0, "app_rw session must not read documents via system actor spoofing"

        # 5. cannot discover all tenants across firm boundary
        cursor.execute("SET LOCAL app.tenant_id = '';")
        cursor.execute("SELECT count(*) FROM tpl.tenant;")
        assert cursor.fetchone()[0] == 0, "app_rw session must not discover tenants via purpose spoofing"

        # 6. cannot insert hearing via system actor
        new_hrg_id = mint_id("hrg")
        cursor.execute("SET LOCAL app.tenant_id = %s;", [tenant_id])
        with pytest.raises(DatabaseError):
            cursor.execute(
                """
                INSERT INTO tpl.hearing (tenant_id, hearing_id, matter_id, date, bench, court_no, item_no, purpose, status, entered_by, observed_at)
                VALUES (%s, %s, %s, %s, 'MUM', '1', '99', 'Fake', 'LISTED', 'system:causelist', now())
                """,
                [tenant_id, new_hrg_id, matter_id, date.today()],
            )


@pytest.mark.django_db(transaction=True, databases=["default", "admin", "owner", "worker"])
def test_system_causelist_actor_never_reads_documents(
    seeded_tenant_with_matter_and_doc: dict[str, str],
) -> None:
    """The system:causelist actor can never read documents from tpl.pdoc even under worker context."""
    from workspace.db import tenant_db_context

    info = seeded_tenant_with_matter_and_doc
    tenant_id = info["tenant_id"]
    matter_id = info["matter_id"]

    # Run under tenant context with system:causelist actor on the worker connection
    with tenant_db_context(
        tenant_id=tenant_id,
        user_id="system:causelist",
        purpose="CAUSELIST_SYNC",
        using="worker",
    ):
        with connections["worker"].cursor() as cursor:
            # 1. Documents are strictly guarded and hidden from system:* actors
            cursor.execute("SELECT count(*) FROM tpl.pdoc WHERE matter_id = %s;", [matter_id])
            assert cursor.fetchone()[0] == 0, "system:causelist must never read documents"

            # 2. Worker can write tpl.hearing
            hrg_worker_id = mint_id("hrg")
            cursor.execute(
                """
                INSERT INTO tpl.hearing (tenant_id, hearing_id, matter_id, date, bench, court_no, item_no, purpose, status, entered_by, observed_at)
                VALUES (%s, %s, %s, %s, 'MUM', '1', '10', 'Legit Sync', 'LISTED', 'system:causelist', now())
                """,
                [tenant_id, hrg_worker_id, matter_id, date.today()],
            )
            cursor.execute("SELECT count(*) FROM tpl.hearing WHERE hearing_id = %s;", [hrg_worker_id])
            assert cursor.fetchone()[0] == 1, "worker with system:causelist must write tpl.hearing"

            # 3. Worker can write tpl.case_candidate
            cnd_worker_id = mint_id("cnd")
            cursor.execute(
                """
                INSERT INTO tpl.case_candidate (tenant_id, candidate_id, matter_id, kind, source, source_ref, case_number_raw, normalized_case_no, status, created_at)
                VALUES (%s, %s, %s, 'HEARING', 'CAUSE_LIST', 'ref_w', 'CP 100/2026', 'CP (IB) 100/MUM/2026', 'PENDING', now())
                """,
                [tenant_id, cnd_worker_id, matter_id],
            )
            cursor.execute("SELECT count(*) FROM tpl.case_candidate WHERE candidate_id = %s;", [cnd_worker_id])
            assert cursor.fetchone()[0] == 1, "worker with system:causelist must write tpl.case_candidate"


@pytest.mark.django_db(transaction=True, databases=["default", "admin", "owner", "worker"])
def test_admin_session_with_cause_list_sync_purpose_gets_nothing_extra(
    seeded_tenant_with_matter_and_doc: dict[str, str],
) -> None:
    """An admin_rw session setting app.purpose=CAUSELIST_SYNC gets nothing extra from the system-sync path."""
    info = seeded_tenant_with_matter_and_doc
    tenant_id = info["tenant_id"]
    matter_id = info["matter_id"]

    with connections["admin"].cursor() as cursor:
        cursor.execute("SELECT SESSION_USER;")
        assert cursor.fetchone()[0] == "admin_rw", "connections['admin'] must run as admin_rw"

        # 1. Setting purpose to CAUSELIST_SYNC under admin_rw does NOT activate the system-sync path
        cursor.execute("SET LOCAL app.tenant_id = %s;", [tenant_id])
        cursor.execute("SET LOCAL app.purpose = 'CAUSELIST_SYNC';")

        # can_read_matter with system:causelist must return false because SESSION_USER != 'worker'
        cursor.execute("SELECT tpl.can_read_matter(%s, 'system:causelist');", [matter_id])
        assert cursor.fetchone()[0] is False, "admin_rw must not activate system-sync path in can_read_matter"

        # can_read_matter with empty user must return false
        cursor.execute("SELECT tpl.can_read_matter(%s, '');", [matter_id])
        assert cursor.fetchone()[0] is False, "admin_rw with empty user must return false in can_read_matter"

        # can_read_matter with unauthorized non-member must return false
        unauth_user_id = mint_id("usr")
        cursor.execute("SELECT tpl.can_read_matter(%s, %s);", [matter_id, unauth_user_id])
        assert cursor.fetchone()[0] is False, "admin_rw with unauthenticated user must return false"
