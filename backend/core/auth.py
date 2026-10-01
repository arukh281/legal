"""Authentication backend and dev-only login for lawyer_brain.

Normative sources:
- docs/mvp/04_stack_and_infra.md §2.10: Authentication (firm SSO)
- Session S03 Directive #1: Dev-only login backend for local/tests, impossible in prod
"""

from __future__ import annotations

from typing import Any, cast

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.http import HttpRequest

from core.db_router import admin_db_context
from workspace.models import AppUser

User = get_user_model()


class DevAuthenticationBackend(BaseBackend):
    """Dev-only authentication backend for local development and tests.

    STRICTLY FORBIDDEN IN PRODUCTION. If settings.DEBUG is False or
    settings.DEV_AUTH_ENABLED is False, authentication immediately fails.
    """

    def authenticate(
        self,
        request: HttpRequest | None = None,
        email: str | None = None,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> Any | None:
        # Hard fail-closed if dev auth is disabled or not in DEBUG mode
        if not getattr(settings, "DEV_AUTH_ENABLED", False) or not settings.DEBUG:
            return None

        if not email and not user_id:
            return None

        with admin_db_context():
            # Look up pre-provisioned AppUser across tenants
            query = AppUser.objects.filter(active=True)
            if email:
                query = query.filter(email=email)
            if user_id:
                query = query.filter(user_id=user_id)

            app_user = query.first()
            if not app_user:
                return None

            # Link/get or create standard Django user for session management
            django_user, _ = User.objects.get_or_create(
                username=app_user.user_id,
                defaults={"email": app_user.email, "is_active": True},
            )
            cast(Any, django_user).app_user = app_user
            return django_user

    def get_user(self, user_id: Any) -> Any | None:
        try:
            django_user = User.objects.get(pk=user_id)
            app_user = AppUser.objects.filter(user_id=django_user.username, active=True).first()
            if app_user:
                cast(Any, django_user).app_user = app_user
            return django_user
        except User.DoesNotExist:
            return None
