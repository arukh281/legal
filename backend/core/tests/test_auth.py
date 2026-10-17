"""Tests for authentication backend, SSO adapters, dev-login endpoint, and prod security checks.

Normative sources:
- docs/mvp/04_stack_and_infra.md §2.10: Single-tenant Entra (tid check), Google (hd check), no self-signup.
- Session S03 Directive #1: Dev login backend strictly impossible in production.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from allauth.core.exceptions import ImmediateHttpResponse
from django.test import Client

from anchor_lib.ids import mint_id
from core.adapters import LawyerBrainAccountAdapter, LawyerBrainSocialAccountAdapter
from core.auth import DevAuthenticationBackend
from core.checks import check_dev_auth_not_in_prod
from core.db_router import admin_db_context
from workspace.models import AppUser, Tenant

pytestmark = pytest.mark.django_db(databases="__all__", transaction=True)


@pytest.fixture(autouse=True)
def enable_dev_auth_in_tests(settings: Any) -> None:
    settings.DEBUG = True
    settings.DEV_AUTH_ENABLED = True


@pytest.fixture
def auth_setup() -> dict[str, Any]:
    with admin_db_context():
        t_id = mint_id("ten")
        domain = f"{t_id}.cyrilshroff.com"
        tenant = Tenant.objects.create(
            tenant_id=t_id,
            name="Cyril Amarchand Mangaldas",
            idp={"kind": "GOOGLE", "domain": domain},
        )

        u_active = AppUser.objects.create(
            tenant_id=t_id,
            user_id=mint_id("usr"),
            email=f"lawyer_{t_id}@cyrilshroff.com",
            idp_subject=f"sub_google_{t_id}",
            firm_role="PARTNER",
            active=True,
        )

        u_inactive = AppUser.objects.create(
            tenant_id=t_id,
            user_id=mint_id("usr"),
            email=f"former_{t_id}@cyrilshroff.com",
            idp_subject=f"sub_google_former_{t_id}",
            firm_role="ASSOCIATE",
            active=False,
        )

        return {
            "tenant": tenant,
            "user_active": u_active,
            "user_inactive": u_inactive,
        }


def test_dev_authentication_backend(auth_setup: dict[str, Any]) -> None:
    backend = DevAuthenticationBackend()
    u_active = auth_setup["user_active"]
    u_inactive = auth_setup["user_inactive"]

    # 1. Authenticate with valid email
    user = backend.authenticate(None, email=u_active.email)
    assert user is not None
    assert user.username == u_active.user_id
    assert user.app_user.email == u_active.email

    # 2. Authenticate with valid user_id
    user2 = backend.authenticate(None, user_id=u_active.user_id)
    assert user2 is not None
    assert user2.username == u_active.user_id

    # 3. Inactive user fails
    assert backend.authenticate(None, email=u_inactive.email) is None

    # 4. Unknown user fails
    assert backend.authenticate(None, email="nonexistent@law.com") is None


def test_dev_auth_fails_closed_when_disabled(auth_setup: dict[str, Any], settings: Any) -> None:
    backend = DevAuthenticationBackend()
    u_active = auth_setup["user_active"]

    # When DEV_AUTH_ENABLED is False, authentication returns None
    settings.DEV_AUTH_ENABLED = False
    assert backend.authenticate(None, email=u_active.email) is None

    # When DEBUG is False, authentication returns None
    settings.DEV_AUTH_ENABLED = True
    settings.DEBUG = False
    assert backend.authenticate(None, email=u_active.email) is None


def test_api_dev_login_endpoint(auth_setup: dict[str, Any]) -> None:
    client = Client()
    u_active = auth_setup["user_active"]
    u_inactive = auth_setup["user_inactive"]

    # Successful dev login
    resp = client.post(
        "/api/auth/dev-login",
        data={"email": u_active.email},
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "authenticated"
    assert data["user_id"] == u_active.user_id
    assert data["tenant_id"] == u_active.tenant_id

    # Inactive user forbidden
    resp2 = client.post(
        "/api/auth/dev-login",
        data={"email": u_inactive.email},
        content_type="application/json",
    )
    assert resp2.status_code == 403


def test_no_self_signup_adapters() -> None:
    account_adapter = LawyerBrainAccountAdapter()
    social_adapter = LawyerBrainSocialAccountAdapter()
    req = MagicMock()

    assert not account_adapter.is_open_for_signup(req)
    assert not social_adapter.is_open_for_signup(req, MagicMock())


def test_social_account_adapter_google_hd_validation(auth_setup: dict[str, Any]) -> None:
    adapter = LawyerBrainSocialAccountAdapter()
    u_active = auth_setup["user_active"]

    tenant = auth_setup["tenant"]
    domain = tenant.idp["domain"]

    # Mock sociallogin with valid Google claims
    sociallogin = MagicMock()
    sociallogin.account.provider = "google"
    sociallogin.account.extra_data = {"email": u_active.email, "hd": domain}
    sociallogin.user.email = u_active.email

    adapter.pre_social_login(MagicMock(), sociallogin)
    assert sociallogin.user.username == u_active.user_id

    # Missing hd claim
    sociallogin_no_hd = MagicMock()
    sociallogin_no_hd.account.provider = "google"
    sociallogin_no_hd.account.extra_data = {"email": u_active.email}
    sociallogin_no_hd.user.email = u_active.email

    with pytest.raises(ImmediateHttpResponse):
        adapter.pre_social_login(MagicMock(), sociallogin_no_hd)

    # Unauthorized domain
    sociallogin_wrong_hd = MagicMock()
    sociallogin_wrong_hd.account.provider = "google"
    sociallogin_wrong_hd.account.extra_data = {"email": "user@gmail.com", "hd": "gmail.com"}
    sociallogin_wrong_hd.user.email = "user@gmail.com"

    with pytest.raises(ImmediateHttpResponse):
        adapter.pre_social_login(MagicMock(), sociallogin_wrong_hd)


def test_check_dev_auth_not_in_prod(settings: Any) -> None:
    # In production (DEBUG=False), DEV_AUTH_ENABLED=True triggers core.E001
    settings.DEBUG = False
    settings.ENVIRONMENT = "production"
    settings.DEV_AUTH_ENABLED = True
    settings.AUTHENTICATION_BACKENDS = ["core.auth.DevAuthenticationBackend"]

    errors = check_dev_auth_not_in_prod()
    error_ids = {e.id for e in errors}
    assert "core.E001" in error_ids
    assert "core.E002" in error_ids


def test_server_decides_dataclass_and_client_cannot_lower(auth_setup: dict[str, Any]) -> None:
    from django.test import RequestFactory

    from core.authz_dependency import AuthzDependency

    factory = RequestFactory()
    dep = AuthzDependency()
    u_active = auth_setup["user_active"]

    # 1. Non-matter request defaults to PUBLIC
    req1 = factory.get("/api/test", HTTP_AUTHORIZATION=f"Bearer {u_active.email}")
    ctx1 = dep.authenticate(req1, u_active.email)
    assert ctx1 is not None
    assert ctx1.dataclass == "PUBLIC"

    # 2. Non-matter request can be raised to PRIVILEGED or TENANT_CONFIDENTIAL by client
    req2 = factory.get(
        "/api/test",
        HTTP_AUTHORIZATION=f"Bearer {u_active.email}",
        HTTP_X_DATACLASS="PRIVILEGED",
    )
    ctx2 = dep.authenticate(req2, u_active.email)
    assert ctx2 is not None
    assert ctx2.dataclass == "PRIVILEGED"

    req2b = factory.get(
        "/api/test",
        HTTP_AUTHORIZATION=f"Bearer {u_active.email}",
        HTTP_X_DATACLASS="TENANT_CONFIDENTIAL",
    )
    ctx2b = dep.authenticate(req2b, u_active.email)
    assert ctx2b is not None
    assert ctx2b.dataclass == "TENANT_CONFIDENTIAL"

    # 3. Matter-scoped request defaults to TENANT_CONFIDENTIAL
    req3 = factory.get(
        "/api/test",
        HTTP_AUTHORIZATION=f"Bearer {u_active.email}",
        HTTP_X_MATTER_ID="mat_01TESTMATTER000000000000",
    )
    ctx3 = dep.authenticate(req3, u_active.email)
    assert ctx3 is not None
    assert ctx3.matter_id == "mat_01TESTMATTER000000000000"
    assert ctx3.dataclass == "TENANT_CONFIDENTIAL"

    # 4. Matter-scoped request CANNOT be lowered to PUBLIC by client
    req4 = factory.get(
        "/api/test",
        HTTP_AUTHORIZATION=f"Bearer {u_active.email}",
        HTTP_X_MATTER_ID="mat_01TESTMATTER000000000000",
        HTTP_X_DATACLASS="PUBLIC",
    )
    ctx4 = dep.authenticate(req4, u_active.email)
    assert ctx4 is not None
    assert ctx4.dataclass == "TENANT_CONFIDENTIAL"

    # 5. Matter-scoped request CAN be raised to PRIVILEGED by client
    req5 = factory.get(
        "/api/test",
        HTTP_AUTHORIZATION=f"Bearer {u_active.email}",
        HTTP_X_MATTER_ID="mat_01TESTMATTER000000000000",
        HTTP_X_DATACLASS="PRIVILEGED",
    )
    ctx5 = dep.authenticate(req5, u_active.email)
    assert ctx5 is not None
    assert ctx5.dataclass == "PRIVILEGED"
