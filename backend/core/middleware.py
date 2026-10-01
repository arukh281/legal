"""Middleware for tenant context lifecycle and RLS session parameter isolation.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §1 item 1, §6
- Session S03 Directive #4: Tenant context leakage prevention and explicit resets
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from django.http import HttpRequest, HttpResponse

from core.db_router import admin_db_context
from workspace.db import reset_db_tenant_context, set_db_tenant_context
from workspace.models import AppUser


class TenantContextMiddleware:
    """Sets PostgreSQL RLS session parameters per request and guarantees cleanup on release."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        app_user: AppUser | None = None

        if hasattr(request, "user") and request.user.is_authenticated:
            app_user = getattr(request.user, "app_user", None)
            if app_user is None:
                with admin_db_context():
                    app_user = AppUser.objects.filter(
                        user_id=request.user.username, active=True
                    ).first()
                if app_user:
                    cast(Any, request.user).app_user = app_user

        # Set tenant session parameters if authenticated user with tenant
        if app_user:
            set_db_tenant_context(
                tenant_id=app_user.tenant_id,
                user_id=app_user.user_id,
                purpose="INTERACTIVE",
            )
        else:
            reset_db_tenant_context()

        try:
            response = self.get_response(request)
            return response
        finally:
            # Guarantees that any connection checkout is completely reset on release
            reset_db_tenant_context()
