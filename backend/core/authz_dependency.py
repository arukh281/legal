"""Django Ninja authorization dependency and security choke point.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §6
- docs/01a_spine_decision_record.md: D9 (ExecutionContext)
- Session S03 Directive #7: Ninja dependency so no endpoint can skip authz
"""

from __future__ import annotations

from typing import Any, cast

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from ninja.security import HttpBearer

from workspace.authz import ExecutionContext
from workspace.db import set_db_tenant_context
from workspace.models import AppUser, Tenant

User = get_user_model()


class AuthzDependency(HttpBearer):
    """Ninja security dependency authenticating requests and binding ExecutionContext."""

    def authenticate(self, request: HttpRequest, token: str) -> ExecutionContext | None:
        # 1. First check if request has Django session-authenticated user
        app_user: AppUser | None = None
        if hasattr(request, "user") and request.user.is_authenticated:
            app_user = getattr(request.user, "app_user", None)
            if app_user is None:
                app_user = AppUser.objects.filter(
                    user_id=request.user.username, active=True
                ).first()

        # 2. If token is provided, check dev token or user_id in dev/test mode
        if not app_user and getattr(settings, "DEV_AUTH_ENABLED", False):
            # Token can be usr_... or email in dev/test
            app_user = AppUser.objects.filter(active=True).filter(models_user_match(token)).first()

        if not app_user or not app_user.active:
            return None

        tenant = Tenant.objects.filter(tenant_id=app_user.tenant_id).first()
        residency_policy = tenant.residency_policy if tenant else "ANY"
        llm_policy = tenant.llm_policy if tenant else {}

        traceparent = request.headers.get("traceparent")

        ctx = ExecutionContext(
            tenant_id=app_user.tenant_id,
            user_id=app_user.user_id,
            firm_role=app_user.firm_role,
            matter_id=request.headers.get("X-Matter-ID"),
            purpose=request.headers.get("X-Purpose", "INTERACTIVE"),
            traceparent=traceparent,
            residency_policy=residency_policy,
            llm_policy=llm_policy,
            dataclass="TENANT_CONFIDENTIAL",
        )

        # Set database session parameters for this request
        set_db_tenant_context(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            purpose=ctx.purpose,
        )

        # Attach to request for view handlers
        cast(Any, request).auth_ctx = ctx
        cast(Any, request).app_user = app_user
        return ctx


def models_user_match(token: str) -> Any:
    from django.db.models import Q

    return Q(user_id=token) | Q(email=token)


authz_required = AuthzDependency()
