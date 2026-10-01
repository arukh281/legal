"""Tests for Django Admin creation and inspection of Tenant, AppUser, and Matter.

Normative sources:
- Session S03 Goal: tenant, user, matter can be created/managed through Django admin.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from anchor_lib.ids import mint_id
from workspace.models import AppUser, Matter, Tenant

User = get_user_model()


@pytest.fixture
def admin_client_logged_in(db: None) -> Client:
    """Superuser admin client."""
    client = Client()
    admin_user = User.objects.create_superuser(
        username="admin_user",
        email="admin@platform.internal",
        password="test_password_1234",
    )
    client.force_login(admin_user)
    return client


def test_admin_tenant_list_and_create(admin_client_logged_in: Client) -> None:
    client = admin_client_logged_in

    # 1. Admin changelist loads
    resp = client.get("/admin/workspace/tenant/")
    assert resp.status_code == 200

    # 2. Create tenant
    resp_create = client.post(
        "/admin/workspace/tenant/add/",
        data={
            "name": "Khaitan & Co",
            "deployment_mode": "D2",
            "residency_policy": "IN_ONLY",
            "llm_policy": "{}",
            "idp": '{"kind": "GOOGLE", "domain": "khaitanco.com"}',
        },
    )
    # Redirects to changelist on successful creation
    assert resp_create.status_code == 302

    tenant = Tenant.objects.filter(name="Khaitan & Co").first()
    assert tenant is not None
    assert tenant.residency_policy == "IN_ONLY"
    assert tenant.tenant_id.startswith("ten_")


def test_admin_app_user_list_and_create(admin_client_logged_in: Client) -> None:
    client = admin_client_logged_in
    t_id = mint_id("ten")
    Tenant.objects.create(
        tenant_id=t_id,
        name="AZB & Partners",
        idp={"kind": "GOOGLE", "domain": "azbpartners.com"},
    )

    # 1. User changelist loads
    resp = client.get("/admin/workspace/adminappuser/")
    assert resp.status_code == 200

    # 2. Create app user via admin
    resp_create = client.post(
        "/admin/workspace/adminappuser/add/",
        data={
            "tenant_id": t_id,
            "email": "partner@azbpartners.com",
            "display_name": "Senior Partner",
            "idp_subject": "sub_azb_partner",
            "firm_role": "PARTNER",
            "active": "on",
        },
    )
    assert resp_create.status_code == 302

    user = AppUser.objects.filter(email="partner@azbpartners.com").first()
    assert user is not None
    assert user.firm_role == "PARTNER"
    assert user.tenant_id == t_id
    assert user.user_id.startswith("usr_")


def test_admin_matter_list_and_create(admin_client_logged_in: Client) -> None:
    client = admin_client_logged_in
    t_id = mint_id("ten")
    Tenant.objects.create(
        tenant_id=t_id,
        name="Trilegal",
        idp={"kind": "GOOGLE", "domain": "trilegal.com"},
    )

    # 1. Matter changelist loads
    resp = client.get("/admin/workspace/adminmatter/")
    assert resp.status_code == 200

    # 2. Create matter via admin
    resp_create = client.post(
        "/admin/workspace/adminmatter/add/",
        data={
            "tenant_id": t_id,
            "title": "Cross-Border M&A",
            "client_role": "PETITIONER",
            "status": "ACTIVE",
            "context_version": 0,
            "membership_version": 0,
            "forum": "{}",
        },
    )
    assert resp_create.status_code == 302

    matter = Matter.objects.filter(title="Cross-Border M&A").first()
    assert matter is not None
    assert matter.tenant_id == t_id
    assert matter.matter_id.startswith("mat_")
