"""Allauth account and social account adapters enforcing pre-provisioning and SSO restrictions.

Normative sources:
- docs/mvp/04_stack_and_infra.md §2.10: Single-tenant Entra (tid check), Google (hd check), no self-signup.
"""

from __future__ import annotations

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.http import HttpRequest, HttpResponseForbidden

from core.db_router import admin_db_context
from workspace.models import AppUser, Tenant


class LawyerBrainAccountAdapter(DefaultAccountAdapter):
    """Enforces no self-signup policy per 04 §2.10."""

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        """Deny all self-signups; users must be pre-provisioned by firm admin."""
        return False


class LawyerBrainSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Enforces tenant-scoped SSO checks (hd for Google, tid for Entra) and user pre-provisioning."""

    def is_open_for_signup(self, request: HttpRequest, sociallogin: SocialLogin) -> bool:
        """Deny social self-signup; only pre-provisioned users may log in."""
        return False

    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin) -> None:
        """Validate IdP claims (hd/tid) against Tenant.idp and verify user is pre-provisioned."""
        with admin_db_context():
            self._do_pre_social_login(request, sociallogin)

    def _do_pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin) -> None:
        provider = sociallogin.account.provider
        extra_data = sociallogin.account.extra_data
        email = sociallogin.user.email or extra_data.get("email")

        if not email:
            raise ImmediateHttpResponse(
                HttpResponseForbidden("SSO authentication failed: email claim is required.")
            )

        # 1. Validate IdP tenant/domain constraints
        if provider == "google":
            hd = extra_data.get("hd")
            if not hd:
                raise ImmediateHttpResponse(
                    HttpResponseForbidden("Google SSO failed: hd (hosted domain) claim missing.")
                )
            tenant = Tenant.objects.filter(idp__kind="GOOGLE", idp__domain=hd).first()
            if not tenant:
                raise ImmediateHttpResponse(
                    HttpResponseForbidden(f"Unauthorized Google domain '{hd}'.")
                )
        elif provider == "microsoft":
            tid = extra_data.get("tid")
            if not tid:
                raise ImmediateHttpResponse(
                    HttpResponseForbidden("Microsoft SSO failed: tid (tenant ID) claim missing.")
                )
            tenant = Tenant.objects.filter(idp__kind="ENTRA", idp__tenant=tid).first()
            if not tenant:
                raise ImmediateHttpResponse(
                    HttpResponseForbidden(f"Unauthorized Microsoft tenant '{tid}'.")
                )
        else:
            raise ImmediateHttpResponse(
                HttpResponseForbidden(f"Unsupported social provider '{provider}'.")
            )

        # 2. Verify pre-provisioned user in tpl.app_user
        app_user = AppUser.objects.filter(
            tenant_id=tenant.tenant_id,
            email__iexact=email,
            active=True,
        ).first()

        if not app_user:
            raise ImmediateHttpResponse(
                HttpResponseForbidden(
                    f"User '{email}' is not pre-provisioned for tenant '{tenant.name}'."
                )
            )

        # Connect the social account to the pre-provisioned user's identifier
        sociallogin.user.username = app_user.user_id
        sociallogin.user.app_user = app_user
