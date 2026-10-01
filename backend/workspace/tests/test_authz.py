"""Tests for authorization single choke point, TEC, and Ninja route coverage.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §6: Authorization (instead of OpenFGA)
- docs/01a_spine_decision_record.md: D9 (Tenant Execution Context)
- Session S03 Directive #7: Ninja dependency so no non-public route can skip authz
"""

from __future__ import annotations

from typing import Any

import pytest
from django.test import Client

from anchor_lib.ids import mint_id
from core.api import api
from core.authz_dependency import authz_required
from workspace.authz import can
from workspace.models import (
    AppUser,
    AuditEvent,
    EthicalWall,
    Matter,
    MatterMember,
    Tenant,
    WallExclusion,
)


@pytest.fixture
def authz_fixture(db: None) -> dict[str, Any]:
    """Create tenant, users, and matters with varying memberships and walls."""
    t_id = mint_id("ten")
    tenant = Tenant.objects.create(
        tenant_id=t_id,
        name="Shardul Amarchand Mangaldas",
        idp={"kind": "GOOGLE", "tenant_or_domain": "sam.com"},
    )

    u_admin = AppUser.objects.create(
        tenant_id=t_id,
        user_id=mint_id("usr"),
        email="admin@sam.com",
        idp_subject="sub_admin",
        firm_role="ADMIN",
        active=True,
    )

    u_lead = AppUser.objects.create(
        tenant_id=t_id,
        user_id=mint_id("usr"),
        email="lead@sam.com",
        idp_subject="sub_lead",
        firm_role="PARTNER",
        active=True,
    )

    u_member = AppUser.objects.create(
        tenant_id=t_id,
        user_id=mint_id("usr"),
        email="member@sam.com",
        idp_subject="sub_member",
        firm_role="ASSOCIATE",
        active=True,
    )

    u_viewer = AppUser.objects.create(
        tenant_id=t_id,
        user_id=mint_id("usr"),
        email="viewer@sam.com",
        idp_subject="sub_viewer",
        firm_role="PARALEGAL",
        active=True,
    )

    u_excluded = AppUser.objects.create(
        tenant_id=t_id,
        user_id=mint_id("usr"),
        email="excluded@sam.com",
        idp_subject="sub_excluded",
        firm_role="PARTNER",
        active=True,
    )

    u_inactive = AppUser.objects.create(
        tenant_id=t_id,
        user_id=mint_id("usr"),
        email="inactive@sam.com",
        idp_subject="sub_inactive",
        firm_role="ASSOCIATE",
        active=False,
    )

    # Matter 1: standard matter
    m1 = Matter.objects.create(
        tenant_id=t_id,
        matter_id=mint_id("mat"),
        title="Tata Sons Restructuring",
        client_role="PETITIONER",
        walled=False,
    )

    # Matter 2: walled matter
    m2 = Matter.objects.create(
        tenant_id=t_id,
        matter_id=mint_id("mat"),
        title="Hostile Takeover Defense",
        client_role="RESPONDENT",
        walled=True,
    )

    # Memberships on m1
    MatterMember.objects.create(
        tenant_id=t_id,
        matter_id=m1.matter_id,
        user_id=u_lead.user_id,
        role="LEAD",
        granted_by=u_admin.user_id,
    )
    MatterMember.objects.create(
        tenant_id=t_id,
        matter_id=m1.matter_id,
        user_id=u_member.user_id,
        role="MEMBER",
        granted_by=u_admin.user_id,
    )
    MatterMember.objects.create(
        tenant_id=t_id,
        matter_id=m1.matter_id,
        user_id=u_viewer.user_id,
        role="VIEWER",
        granted_by=u_admin.user_id,
    )

    # Memberships on m2 (lead only)
    MatterMember.objects.create(
        tenant_id=t_id,
        matter_id=m2.matter_id,
        user_id=u_lead.user_id,
        role="LEAD",
        granted_by=u_admin.user_id,
    )

    # Ethical wall on m2 excluding u_excluded
    wall = EthicalWall.objects.create(
        tenant_id=t_id,
        wall_id=mint_id("ewl"),
        matter_id=m2.matter_id,
        basis="Prior representation of bidder",
        created_by=u_admin.user_id,
    )
    WallExclusion.objects.create(
        tenant_id=t_id,
        wall_id=wall.wall_id,
        user_id=u_excluded.user_id,
    )

    return {
        "tenant": tenant,
        "admin": u_admin,
        "lead": u_lead,
        "member": u_member,
        "viewer": u_viewer,
        "excluded": u_excluded,
        "inactive": u_inactive,
        "matter_std": m1,
        "matter_walled": m2,
    }


def test_inactive_user_is_always_denied(authz_fixture: dict[str, Any]) -> None:
    u = authz_fixture["inactive"]
    m = authz_fixture["matter_std"]
    assert not can(u, "read", m)
    assert not can(u, "write", m)


def test_matter_member_roles(authz_fixture: dict[str, Any]) -> None:
    lead = authz_fixture["lead"]
    member = authz_fixture["member"]
    viewer = authz_fixture["viewer"]
    m = authz_fixture["matter_std"]

    # VIEWER: reads only
    assert can(viewer, "read", m)
    assert can(viewer, "view", m)
    assert not can(viewer, "write", m)
    assert not can(viewer, "approve_export", m)

    # MEMBER: reads and writes
    assert can(member, "read", m)
    assert can(member, "write", m)
    assert not can(member, "manage_members", m)

    # LEAD: reads, writes, manages members, approves exports
    assert can(lead, "read", m)
    assert can(lead, "write", m)
    assert can(lead, "manage_members", m)
    assert can(lead, "approve_export", m)


def test_firm_admin_on_walled_and_unwalled_matters(authz_fixture: dict[str, Any]) -> None:
    admin = authz_fixture["admin"]
    m_std = authz_fixture["matter_std"]
    m_walled = authz_fixture["matter_walled"]

    # Standard non-walled matter: firm admin has access
    assert can(admin, "read", m_std)

    # Walled matter: firm ADMIN can manage membership, but CANNOT read walled content without membership
    assert can(admin, "manage_members", m_walled)
    assert not can(admin, "read", m_walled)
    assert not can(admin, "write", m_walled)


def test_ethical_wall_exclusion_deny_first_and_audits(authz_fixture: dict[str, Any]) -> None:
    excluded = authz_fixture["excluded"]
    m_walled = authz_fixture["matter_walled"]

    # Even if excluded user has partner role, ethical wall denies immediately
    assert not can(excluded, "read", m_walled)

    # Check that WALL_VIOLATION_ATTEMPT audit row was recorded
    audit_events = list(
        AuditEvent.objects.filter(
            tenant_id=excluded.tenant_id,
            action="WALL_VIOLATION_ATTEMPT",
            matter_id=m_walled.matter_id,
        )
    )
    assert len(audit_events) == 1
    event = audit_events[0]
    assert event.actor == excluded.user_id
    assert event.decision == "DENY"
    assert isinstance(event.detail, dict)
    assert event.detail.get("denial_reason") == "WALL_EXCLUSION"


def test_api_me_unauthenticated_returns_401(db: None) -> None:
    client = Client()
    resp = client.get("/api/me")
    assert resp.status_code == 401


def test_api_me_authenticated_returns_profile(authz_fixture: dict[str, Any]) -> None:
    client = Client()
    u = authz_fixture["lead"]
    resp = client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {u.user_id}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == u.user_id
    assert data["email"] == u.email
    assert data["tenant_id"] == u.tenant_id
    assert data["firm_role"] == u.firm_role


def test_all_ninja_routes_enforce_authz_unless_allowlisted() -> None:
    """Directive #7: Every registered Ninja route must require auth unless in explicit allowlist."""
    PUBLIC_ALLOWLIST = {
        ("/health", "GET"),
        ("/auth/dev-login", "POST"),
    }

    routes_checked = 0

    def check_router(router: Any, prefix: str = "") -> None:
        nonlocal routes_checked
        for path, path_ops in router.path_operations.items():
            full_path = f"{prefix}{path}"
            for op in path_ops.operations:
                for method in op.methods:
                    routes_checked += 1
                    route_key = (full_path, method.upper())
                    if route_key in PUBLIC_ALLOWLIST:
                        continue

                    # Non-public routes must have authz dependency
                    has_auth = False
                    for auth_cb in op.auth_callbacks:
                        if auth_cb is authz_required or isinstance(auth_cb, type(authz_required)):
                            has_auth = True
                            break
                        # In case a tuple or list of auth dependencies is used
                        if hasattr(auth_cb, "__iter__"):
                            for cb in auth_cb:
                                if cb is authz_required or isinstance(cb, type(authz_required)):
                                    has_auth = True
                                    break

                    assert has_auth, (
                        f"Route {method} {full_path} lacks authz dependency and is not in PUBLIC_ALLOWLIST!"
                    )

        for sub_prefix, sub_router in router._routers:
            check_router(sub_router, f"{prefix}/{sub_prefix}".rstrip("/"))

    for prefix, router in api._routers:
        check_router(router, prefix)

    assert routes_checked >= 3
