"""System checks enforcing runtime security invariants.

Normative sources:
- Session S03 Directive #1: Dev login backend strictly impossible in production
- Session S03 Directive #3: Web process must connect as app_rw, never as superuser or BYPASSRLS
"""

from __future__ import annotations

import os
from typing import Any

from django.conf import settings
from django.core.checks import CheckMessage, Error, Tags, Warning, register
from django.db import connection, connections


@register(Tags.security)
def check_dev_auth_not_in_prod(app_configs: Any = None, **kwargs: Any) -> list[CheckMessage]:
    """Ensure DevAuthenticationBackend cannot be enabled in production settings."""
    errors: list[CheckMessage] = []
    is_prod = not settings.DEBUG or getattr(settings, "ENVIRONMENT", "") == "production"

    if is_prod and getattr(settings, "DEV_AUTH_ENABLED", False):
        errors.append(
            Error(
                "DEV_AUTH_ENABLED must be False in production.",
                hint="Remove or disable DEV_AUTH_ENABLED in production settings.",
                id="core.E001",
            )
        )

    backends = getattr(settings, "AUTHENTICATION_BACKENDS", [])
    if is_prod and "core.auth.DevAuthenticationBackend" in backends:
        errors.append(
            Error(
                "DevAuthenticationBackend is registered in production AUTHENTICATION_BACKENDS.",
                hint="DevAuthenticationBackend must only be enabled in local and test environments.",
                id="core.E002",
            )
        )

    return errors


@register(Tags.security)
def check_runtime_db_role(
    app_configs: Any = None, using: str = "default", **kwargs: Any
) -> list[CheckMessage]:
    """Ensure the web runtime role is not a superuser and does not possess BYPASSRLS (Directive #3)."""
    errors: list[CheckMessage] = []

    # Only enforce for web server runtime, not during migrations or celery/worker
    role = os.environ.get("DJANGO_ROLE", "web")
    enforce_check = getattr(settings, "ENFORCE_RUNTIME_DB_ROLE_CHECK", False) or (
        role == "web" and not settings.DEBUG
    )

    if not enforce_check:
        return []

    try:
        conn = connections[using] if using in connections else connection
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT rolname, rolsuper, rolbypassrls
                FROM pg_roles
                WHERE rolname = current_user;
                """
            )
            row = cursor.fetchone()
            if row:
                rolname, rolsuper, rolbypassrls = row
                if rolsuper:
                    errors.append(
                        Error(
                            f"Web process connected as database superuser '{rolname}'. "
                            "Superusers bypass Row Level Security even with FORCE ROW LEVEL SECURITY.",
                            hint="Configure database connection to use 'app_rw' role.",
                            id="core.E003",
                        )
                    )
                if rolbypassrls:
                    errors.append(
                        Error(
                            f"Web process connected as role '{rolname}' with BYPASSRLS privilege. "
                            "Web processes must connect as 'app_rw' without BYPASSRLS.",
                            hint="Ensure web connection uses 'app_rw' which has NOBYPASSRLS.",
                            id="core.E004",
                        )
                    )
    except Exception as exc:
        # If DB is not reachable during check, warn rather than crash system check
        errors.append(
            Warning(
                f"Could not verify runtime database role: {exc}",
                id="core.W001",
            )
        )

    return errors
