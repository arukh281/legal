"""Django Ninja API configuration, health, dev-auth, and protected endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from django.conf import settings
from django.contrib.auth import login
from django.db import connection
from django.http import HttpRequest
from ninja import NinjaAPI, Schema
from ninja.errors import HttpError

from core.authz_dependency import authz_required
from workspace.authz import ExecutionContext
from workspace.models import AppUser

api = NinjaAPI(
    title="Lawyer Brain API",
    version="1.0.0",
    description="Corporate-law legal intelligence platform API",
    urls_namespace="api",
)


class HealthResponse(Schema):
    status: str
    database: str
    schemas: list[str]
    timestamp: str


@api.get("/health", response=HealthResponse, tags=["Health"])
def health_check(request: HttpRequest) -> dict[str, Any]:
    """Health check validating database connectivity and schema existence."""
    schemas_found: list[str] = []
    db_status = "connected"

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name IN ('plc', 'tpl', 'ops')
                ORDER BY schema_name;
                """
            )
            rows = cursor.fetchall()
            schemas_found = [r[0] for r in rows]
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "schemas": schemas_found,
        "timestamp": datetime.now(UTC).isoformat(),
    }


class DevLoginRequest(Schema):
    email: str | None = None
    user_id: str | None = None


class DevLoginResponse(Schema):
    status: str
    user_id: str
    email: str
    tenant_id: str
    firm_role: str


@api.post("/auth/dev-login", response=DevLoginResponse, tags=["Auth"])
def dev_login(request: HttpRequest, payload: DevLoginRequest) -> dict[str, Any]:
    """Dev-only login endpoint for local development and integration tests.

    STRICTLY FORBIDDEN IN PRODUCTION. Refuses to execute if DEV_AUTH_ENABLED is False
    or settings.DEBUG is False.
    """
    if not getattr(settings, "DEV_AUTH_ENABLED", False) or not settings.DEBUG:
        raise HttpError(403, "Dev login is disabled in this environment.")

    query = AppUser.objects.filter(active=True)
    if payload.email:
        query = query.filter(email=payload.email)
    elif payload.user_id:
        query = query.filter(user_id=payload.user_id)
    else:
        raise HttpError(400, "Provide either email or user_id.")

    app_user = query.first()
    if not app_user:
        raise HttpError(403, "User not found or inactive.")

    from django.contrib.auth import get_user_model

    User = get_user_model()
    django_user, _ = User.objects.get_or_create(
        username=app_user.user_id,
        defaults={"email": app_user.email, "is_active": True},
    )
    cast(Any, django_user).app_user = app_user
    login(request, django_user, backend="core.auth.DevAuthenticationBackend")

    return {
        "status": "authenticated",
        "user_id": app_user.user_id,
        "email": app_user.email,
        "tenant_id": app_user.tenant_id,
        "firm_role": app_user.firm_role,
    }


class UserProfileResponse(Schema):
    user_id: str
    email: str
    tenant_id: str
    firm_role: str
    residency_policy: str


@api.get("/me", response=UserProfileResponse, auth=authz_required, tags=["Identity"])
def get_current_user_profile(request: HttpRequest) -> dict[str, Any]:
    """Protected profile endpoint resolving current ExecutionContext."""
    ctx: ExecutionContext = cast(Any, request).auth_ctx
    app_user: AppUser = cast(Any, request).app_user

    return {
        "user_id": ctx.user_id,
        "email": app_user.email,
        "tenant_id": ctx.tenant_id,
        "firm_role": ctx.firm_role,
        "residency_policy": ctx.residency_policy,
    }
