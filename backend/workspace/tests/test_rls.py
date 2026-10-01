"""Tests for PostgreSQL Row Level Security (RLS) enforcement on tpl tables.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §1 item 1, §6
- Session S03 Directive #3: RLS tests must execute under app_rw
- Session S03 Directive #4: Connection reuse test ensuring no tenant context leakage
"""

from __future__ import annotations

import pathlib
import re

import pytest
from django.db import connection, connections, transaction

from anchor_lib.ids import mint_id
from workspace.db import tenant_db_context

pytestmark = pytest.mark.django_db(
    databases=["default", "owner", "admin", "worker"], transaction=True
)


@pytest.fixture
def rls_setup() -> dict[str, str]:
    """Create test tenants, users, and matters for RLS testing."""
    t1_id = mint_id("ten")
    t2_id = mint_id("ten")

    u1_id = mint_id("usr")
    u2_id = mint_id("usr")

    m1_id = mint_id("mat")
    m2_id = mint_id("mat")

    # Use owner connection (superuser postgres) to insert raw fixture data bypassing RLS
    with transaction.atomic(using="owner"):
        with connections["owner"].cursor() as cursor:
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
                VALUES (%s, %s, %s, 'Alice', %s, 'PARTNER', true),
                       (%s, %s, %s, 'Bob', %s, 'PARTNER', true);
                """,
                [
                    t1_id,
                    u1_id,
                    f"alice_{t1_id}@alpha.in",
                    f"sub-alice-{t1_id}",
                    t2_id,
                    u2_id,
                    f"bob_{t2_id}@beta.in",
                    f"sub-bob-{t2_id}",
                ],
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
    """Directive #2: A worker job for Tenant A followed by a job for Tenant B on the same connection.

    Verifies that a worker connected as the real 'worker' role (which has BYPASSRLS)
    transitions to non-bypass role 'app_rw' under tenant_db_context(), preventing Tenant B
    from seeing Tenant A's rows on connection reuse.
    """
    t1_id = rls_setup["t1_id"]
    t2_id = rls_setup["t2_id"]
    u1_id = rls_setup["u1_id"]
    u2_id = rls_setup["u2_id"]

    with connections["worker"].cursor() as cursor:
        # Confirm that the baseline worker role has BYPASSRLS
        cursor.execute("SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user;")
        assert cursor.fetchone()[0] is True, (
            "worker role must possess BYPASSRLS for cross-tenant tasks"
        )

        # 1. Job 1 runs for Tenant A on this worker connection
        with tenant_db_context(
            tenant_id=t1_id, user_id=u1_id, purpose="JOB_RUNNER", using="worker"
        ):
            # Inside tenant context, role is transitioned to app_rw (NOBYPASSRLS)
            cursor.execute(
                "SELECT current_user, rolbypassrls FROM pg_roles WHERE rolname = current_user;"
            )
            cur_user, bypass = cursor.fetchone()
            assert cur_user == "app_rw"
            assert bypass is False, "Tenant-scoped job must run under NOBYPASSRLS"

            cursor.execute("SELECT tenant_id, matter_id FROM tpl.matter;")
            rows_a = cursor.fetchall()
            assert len(rows_a) == 1
            assert rows_a[0][0] == t1_id

        # 2. Job 2 runs for Tenant B reusing the SAME worker connection
        with tenant_db_context(
            tenant_id=t2_id, user_id=u2_id, purpose="JOB_RUNNER", using="worker"
        ):
            cursor.execute(
                "SELECT current_user, rolbypassrls FROM pg_roles WHERE rolname = current_user;"
            )
            cur_user, bypass = cursor.fetchone()
            assert cur_user == "app_rw"
            assert bypass is False

            cursor.execute("SELECT tenant_id, matter_id FROM tpl.matter;")
            rows_b = cursor.fetchall()
            # Must only see Tenant B's matters, never Tenant A's!
            assert all(r[0] == t2_id for r in rows_b)
            assert not any(r[0] == t1_id for r in rows_b)

            # Explicit query for Tenant A rows inside Job B must return 0 rows under RLS
            cursor.execute("SELECT * FROM tpl.matter WHERE tenant_id = %s;", [t1_id])
            assert len(cursor.fetchall()) == 0

        # 3. Post-job state on connection restores role back to worker
        cursor.execute(
            "SELECT current_user, rolbypassrls FROM pg_roles WHERE rolname = current_user;"
        )
        cur_user, bypass = cursor.fetchone()
        assert cur_user == "worker"
        assert bypass is True, "Worker connection must restore worker role after job completion"


def test_session_variable_names_parity_with_rls_policies_and_spec() -> None:
    """Session variable names in db.py, middleware, and live PostgreSQL RLS policies

    must strictly adhere to docs/mvp/03_data_model_and_contracts.md §6:
    - app.tenant_id
    - app.user_id
    - app.purpose
    Fails if any policy, middleware, or db helper uses divergent names
    (e.g., app.current_tenant_id, app.current_user_id, app.current_purpose).
    """
    canonical_session_vars = {"app.tenant_id", "app.user_id", "app.purpose"}
    divergent_names = {
        "app.current_tenant_id",
        "app.current_user_id",
        "app.current_purpose",
        "app.current_tenant",
    }

    # 1. Inspect live PostgreSQL RLS policies in tpl schema
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT schemaname, tablename, policyname, qual, with_check
            FROM pg_policies
            WHERE schemaname = 'tpl';
            """
        )
        policies = cursor.fetchall()
        assert len(policies) > 0, "At least one RLS policy must be active in tpl schema"

        live_policy_session_vars: set[str] = set()
        for _schema, tbl, policy, qual, with_check in policies:
            combined_sql = f"{qual or ''} {with_check or ''}"
            # Extract all current_setting('...', ...) calls
            found = set(re.findall(r"current_setting\('([^':]+)'", combined_sql))
            live_policy_session_vars.update(found)

            # Assert no divergent name is used in any active policy definition
            for bad_name in divergent_names:
                assert bad_name not in combined_sql, (
                    f"Policy {policy} on {tbl} references invalid variable name '{bad_name}'"
                )

        # Active policies must check session variables and must be a subset of the canonical spec
        assert "app.tenant_id" in live_policy_session_vars, (
            "RLS policies must reference app.tenant_id"
        )
        assert live_policy_session_vars.issubset(canonical_session_vars), (
            f"Live RLS policies reference unexpected session variables: {live_policy_session_vars - canonical_session_vars}"
        )

    # 2. Inspect backend/workspace/db.py source code for session variable names
    import workspace.db as db_mod

    db_path = pathlib.Path(db_mod.__file__)
    db_source = db_path.read_text(encoding="utf-8")

    # Assert no divergent names in db.py source
    for bad_name in divergent_names:
        assert bad_name not in db_source, (
            f"workspace/db.py must not reference divergent name '{bad_name}'"
        )

    # Extract all SET app.X and RESET app.X from db.py
    set_vars = set(re.findall(r"SET\s+(app\.[a-z_]+)", db_source))
    reset_vars = set(re.findall(r"RESET\s+(app\.[a-z_]+)", db_source))

    assert set_vars == canonical_session_vars, (
        f"workspace/db.py SET statements differ from canonical specification: {set_vars} != {canonical_session_vars}"
    )
    assert reset_vars == canonical_session_vars, (
        f"workspace/db.py RESET statements differ from canonical specification: {reset_vars} != {canonical_session_vars}"
    )

    # 3. Inspect backend/core/middleware.py source code
    import core.middleware as mw_mod

    mw_path = pathlib.Path(mw_mod.__file__)
    mw_source = mw_path.read_text(encoding="utf-8")
    for bad_name in divergent_names:
        assert bad_name not in mw_source, (
            f"core/middleware.py must not reference divergent name '{bad_name}'"
        )

    # 4. Runtime functional verification on live connection
    with tenant_db_context(
        tenant_id="ten_testcanonical", user_id="usr_testcanonical", purpose="PARITY_TEST"
    ):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    current_setting('app.tenant_id', true),
                    current_setting('app.user_id', true),
                    current_setting('app.purpose', true);
                """
            )
            t, u, p = cursor.fetchone()
            assert t == "ten_testcanonical"
            assert u == "usr_testcanonical"
            assert p == "PARITY_TEST"

            # Divergent names must be completely unset
            for bad_name in divergent_names:
                cursor.execute(f"SELECT current_setting('{bad_name}', true);")
                val = cursor.fetchone()[0]
                assert val in (None, ""), f"Divergent variable '{bad_name}' must be unset"

    # Post-context: canonical variables must be reset
    with connection.cursor() as cursor:
        for var in canonical_session_vars:
            cursor.execute(f"SELECT current_setting('{var}', true);")
            val = cursor.fetchone()[0]
            assert val in (None, ""), (
                f"Canonical variable '{var}' must be reset after exiting context"
            )
