"""PostgreSQL connection session settings manager for multi-tenant RLS.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §1 item 1, §6
- Session S03 Directive #4: Tenant context leakage prevention and explicit resets
- Session S03 follow-up Directive #2: Scoped elevation and multi-connection support
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from django.db import connections


def set_db_tenant_context(
    tenant_id: str | None,
    user_id: str | None = None,
    purpose: str = "INTERACTIVE",
    using: str = "default",
) -> None:
    """Set PostgreSQL session parameters app.tenant_id, app.user_id, app.purpose and enforce app_rw role."""
    conn = connections[using]
    with conn.cursor() as cursor:
        if tenant_id:
            # Enforce non-bypass role app_rw for all tenant-scoped work (Directive #2)
            cursor.execute("SET ROLE app_rw;")
            cursor.execute("SET app.tenant_id = %s", [tenant_id])
        else:
            cursor.execute("RESET ROLE;")
            cursor.execute("RESET app.tenant_id")

        if user_id:
            cursor.execute("SET app.user_id = %s", [user_id])
        else:
            cursor.execute("RESET app.user_id")

        if purpose:
            cursor.execute("SET app.purpose = %s", [purpose])
        else:
            cursor.execute("RESET app.purpose")


def reset_db_tenant_context(using: str = "default") -> None:
    """Reset PostgreSQL session parameters and restore connection role to prevent cross-request leakage."""
    conn = connections[using]
    with conn.cursor() as cursor:
        cursor.execute("RESET ROLE;")
        cursor.execute("RESET app.tenant_id")
        cursor.execute("RESET app.user_id")
        cursor.execute("RESET app.purpose")


@contextmanager
def tenant_db_context(
    tenant_id: str | None,
    user_id: str | None = None,
    purpose: str = "INTERACTIVE",
    using: str = "default",
) -> Generator[None]:
    """Context manager setting DB session parameters and guaranteeing clean reset/restore on exit."""
    conn = connections[using]
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT current_setting('app.tenant_id', true), current_setting('app.user_id', true), current_setting('app.purpose', true)"
        )
        prev_tenant, prev_user, prev_purpose = cursor.fetchone()

    set_db_tenant_context(tenant_id=tenant_id, user_id=user_id, purpose=purpose, using=using)
    try:
        yield
    finally:
        with conn.cursor() as cursor:
            if prev_tenant:
                cursor.execute("SET ROLE app_rw;")
                cursor.execute("SET app.tenant_id = %s", [prev_tenant])
                if prev_user:
                    cursor.execute("SET app.user_id = %s", [prev_user])
                else:
                    cursor.execute("RESET app.user_id")
                if prev_purpose:
                    cursor.execute("SET app.purpose = %s", [prev_purpose])
                else:
                    cursor.execute("RESET app.purpose")
            else:
                cursor.execute("RESET ROLE;")
                cursor.execute("RESET app.tenant_id")
                cursor.execute("RESET app.user_id")
                cursor.execute("RESET app.purpose")

