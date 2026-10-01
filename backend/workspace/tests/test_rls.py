"""Tests for PostgreSQL Row Level Security (RLS) enforcement on tpl tables.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §1 item 1, §6
- Session S03 Directive #3: RLS tests must execute under app_rw
- Session S03 Directive #4: Connection reuse test ensuring no tenant context leakage
"""

from __future__ import annotations

import pytest
from django.db import connection

from anchor_lib.ids import mint_id
from workspace.db import tenant_db_context


@pytest.fixture
def rls_setup(db: None) -> dict[str, str]:
    """Create test tenants, users, and matters for RLS testing."""
    # Ensure roles exist and permissions are granted
    with connection.cursor() as cursor:
        cursor.execute("RESET ROLE;")

    t1_id = mint_id("ten")
    t2_id = mint_id("ten")

    u1_id = mint_id("usr")
    u2_id = mint_id("usr")

    m1_id = mint_id("mat")
    m2_id = mint_id("mat")

    with connection.cursor() as cursor:
        # Insert raw data without RLS as superuser/owner
        cursor.execute(
            """
            INSERT INTO tpl.tenant (tenant_id, name, deployment_mode, residency_policy, llm_policy, idp, created_at)
            VALUES (%s, %s, 'D2', 'ANY', '{}', '{"kind":"GOOGLE"}', now()),
                   (%s, %s, 'D2', 'ANY', '{}', '{"kind":"GOOGLE"}', now());
            """,
            [t1_id, "Tenant Alpha", t2_id, "Tenant Beta"],
        )
        cursor.execute(
            """
            INSERT INTO tpl.app_user (tenant_id, user_id, email, display_name, idp_subject, firm_role, active)
            VALUES (%s, %s, 'alice@alpha.in', 'Alice', 'sub-alice', 'PARTNER', true),
                   (%s, %s, 'bob@beta.in', 'Bob', 'sub-bob', 'PARTNER', true);
            """,
            [t1_id, u1_id, t2_id, u2_id],
        )
        cursor.execute(
            """
            INSERT INTO tpl.matter (tenant_id, matter_id, title, client_role, status, walled, created_at)
            VALUES (%s, %s, 'Alpha Matter 1', 'PETITIONER', 'ACTIVE', false, now()),
                   (%s, %s, 'Beta Matter 1', 'RESPONDENT', 'ACTIVE', false, now());
            """,
            [t1_id, m1_id, t2_id, m2_id],
        )
        # Grant membership
        cursor.execute(
            """
            INSERT INTO tpl.matter_member (tenant_id, matter_id, user_id, role, granted_by, granted_at)
            VALUES (%s, %s, %s, 'LEAD', 'system', now()),
                   (%s, %s, %s, 'LEAD', 'system', now());
            """,
            [t1_id, m1_id, u1_id, t2_id, m2_id, u2_id],
        )

    return {
        "t1_id": t1_id,
        "t2_id": t2_id,
        "u1_id": u1_id,
        "u2_id": u2_id,
        "m1_id": m1_id,
        "m2_id": m2_id,
    }


def test_query_without_tenant_setting_returns_nothing_under_app_rw(
    rls_setup: dict[str, str],
) -> None:
    """A query without the app.tenant_id setting returns 0 rows rather than everything."""
    with connection.cursor() as cursor:
        cursor.execute("SET ROLE app_rw;")
        try:
            cursor.execute("RESET app.tenant_id;")
            cursor.execute("RESET app.user_id;")

            cursor.execute("SELECT count(*) FROM tpl.tenant;")
            count = cursor.fetchone()[0]
            assert count == 0, f"Expected 0 tenant rows without tenant setting, got {count}"

            cursor.execute("SELECT count(*) FROM tpl.matter;")
            count = cursor.fetchone()[0]
            assert count == 0, f"Expected 0 matter rows without tenant setting, got {count}"
        finally:
            cursor.execute("RESET ROLE;")


def test_tenant_isolation_under_app_rw(rls_setup: dict[str, str]) -> None:
    """A user in Tenant Alpha cannot read Tenant Beta rows even with raw SQL through app_rw."""
    t1_id = rls_setup["t1_id"]
    t2_id = rls_setup["t2_id"]
    u1_id = rls_setup["u1_id"]

    with connection.cursor() as cursor:
        cursor.execute("SET ROLE app_rw;")
        try:
            # Set context to Tenant Alpha
            cursor.execute("SET app.tenant_id = %s;", [t1_id])
            cursor.execute("SET app.user_id = %s;", [u1_id])

            # Query all matters
            cursor.execute("SELECT tenant_id, matter_id FROM tpl.matter;")
            rows = cursor.fetchall()

            # Must only see Tenant Alpha matters
            assert len(rows) == 1
            assert rows[0][0] == t1_id
            assert rows[0][1] == rls_setup["m1_id"]

            # Explicit query trying to select Tenant Beta rows
            cursor.execute("SELECT * FROM tpl.matter WHERE tenant_id = %s;", [t2_id])
            assert len(cursor.fetchall()) == 0

            cursor.execute("SELECT * FROM tpl.app_user WHERE tenant_id = %s;", [t2_id])
            assert len(cursor.fetchall()) == 0
        finally:
            cursor.execute("RESET app.tenant_id;")
            cursor.execute("RESET app.user_id;")
            cursor.execute("RESET ROLE;")


def test_connection_reuse_leakage_prevention(rls_setup: dict[str, str]) -> None:
    """Directive #4: Request 1 (tenant A) and Request 2 (no tenant) reusing the same connection.

    Verifies that resetting connection context guarantees Request 2 sees nothing.
    """
    t1_id = rls_setup["t1_id"]
    u1_id = rls_setup["u1_id"]

    with connection.cursor() as cursor:
        cursor.execute("SET ROLE app_rw;")
        try:
            # Request 1 executes with Tenant Alpha context
            with tenant_db_context(tenant_id=t1_id, user_id=u1_id):
                cursor.execute("SELECT count(*) FROM tpl.matter;")
                assert cursor.fetchone()[0] == 1

            # Request 2 executes without tenant context on the same database connection
            cursor.execute("SELECT count(*) FROM tpl.matter;")
            assert cursor.fetchone()[0] == 0

            cursor.execute("SELECT count(*) FROM tpl.app_user;")
            assert cursor.fetchone()[0] == 0
        finally:
            cursor.execute("RESET ROLE;")


def test_worker_job_tenant_isolation_on_connection_reuse(rls_setup: dict[str, str]) -> None:
    """Directive #3: A worker job for Tenant A followed by a job for Tenant B on the same connection.

    Verifies that worker jobs correctly set and reset tenant context and Tenant B's job cannot see Tenant A's rows.
    """
    t1_id = rls_setup["t1_id"]
    t2_id = rls_setup["t2_id"]
    u1_id = rls_setup["u1_id"]
    u2_id = rls_setup["u2_id"]

    with connection.cursor() as cursor:
        cursor.execute("SET ROLE app_rw;")
        try:
            # 1. Job 1 runs for Tenant A on this worker connection
            with tenant_db_context(tenant_id=t1_id, user_id=u1_id, purpose="JOB_RUNNER"):
                cursor.execute("SELECT tenant_id, matter_id FROM tpl.matter;")
                rows_a = cursor.fetchall()
                assert len(rows_a) == 1
                assert rows_a[0][0] == t1_id

            # 2. Job 2 runs for Tenant B reusing the SAME connection
            with tenant_db_context(tenant_id=t2_id, user_id=u2_id, purpose="JOB_RUNNER"):
                cursor.execute("SELECT tenant_id, matter_id FROM tpl.matter;")
                rows_b = cursor.fetchall()
                # Must only see Tenant B's matters (or 0 if none created for B), never Tenant A's!
                assert all(r[0] == t2_id for r in rows_b)
                assert not any(r[0] == t1_id for r in rows_b)

                # Explicit query for Tenant A rows inside Job B must return 0 rows
                cursor.execute("SELECT * FROM tpl.matter WHERE tenant_id = %s;", [t1_id])
                assert len(cursor.fetchall()) == 0

            # 3. Post-job state on connection has context completely cleared
            cursor.execute("SELECT count(*) FROM tpl.matter;")
            assert cursor.fetchone()[0] == 0
        finally:
            cursor.execute("RESET ROLE;")
