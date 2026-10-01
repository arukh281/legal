"""PostgreSQL connection session settings manager for multi-tenant RLS.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §1 item 1, §6
- Session S03 Directive #4: Tenant context leakage prevention and explicit resets
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from django.db import connection


def set_db_tenant_context(
    tenant_id: str | None,
    user_id: str | None = None,
    purpose: str = "INTERACTIVE",
) -> None:
    """Set PostgreSQL session parameters app.tenant_id, app.user_id, app.purpose."""
    with connection.cursor() as cursor:
        if tenant_id:
            cursor.execute("SET app.tenant_id = %s", [tenant_id])
        else:
            cursor.execute("RESET app.tenant_id")

        if user_id:
            cursor.execute("SET app.user_id = %s", [user_id])
        else:
            cursor.execute("RESET app.user_id")

        if purpose:
            cursor.execute("SET app.purpose = %s", [purpose])
        else:
            cursor.execute("RESET app.purpose")


def reset_db_tenant_context() -> None:
    """Reset PostgreSQL session parameters to prevent cross-request leakage."""
    with connection.cursor() as cursor:
        cursor.execute("RESET app.tenant_id")
        cursor.execute("RESET app.user_id")
        cursor.execute("RESET app.purpose")


@contextmanager
def tenant_db_context(
    tenant_id: str | None,
    user_id: str | None = None,
    purpose: str = "INTERACTIVE",
) -> Generator[None]:
    """Context manager setting DB session parameters and guaranteeing clean reset on exit."""
    set_db_tenant_context(tenant_id=tenant_id, user_id=user_id, purpose=purpose)
    try:
        yield
    finally:
        reset_db_tenant_context()
