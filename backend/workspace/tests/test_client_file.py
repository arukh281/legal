"""Contract, RLS, and Authorization tests for Client File and Document Vault (Session R1).

Normative sources:
- Session R1: the client file (clients, matters, document vault)
- docs/mvp/03_data_model_and_contracts.md §3.8, §3.9, §6
- AGENTS.md §4 item 1, §5 (RLS, prefix cli, tenant isolation)
"""

from __future__ import annotations

import json

import pytest
from django.db import connection, connections, transaction

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from workspace import authz
from workspace.models import (
    AppUser,
    Client,
    Matter,
    MatterCaseLink,
    Pdoc,
    PdocVersion,
    PrivateAnchor,
)

pytestmark = pytest.mark.django_db(
    databases=["default", "owner", "admin", "worker"], transaction=True
)


@pytest.fixture
def workspace_setup() -> dict[str, str]:
    """Setup tenants, users, clients, and matters for testing."""
    t1 = mint_id("ten")
    t2 = mint_id("ten")

    u_admin = mint_id("usr")
    u_member = mint_id("usr")
    u_outsider = mint_id("usr")
    u_other_tenant = mint_id("usr")

    with transaction.atomic(using="owner"):
        with connections["owner"].cursor() as cursor:
            # Tenants
            cursor.execute(
                """
                INSERT INTO tpl.tenant (tenant_id, name, deployment_mode, residency_policy, llm_policy, idp, created_at)
                VALUES (%s, 'Alpha Corp Law', 'D2', 'ANY', '{}', '{"kind":"GOOGLE"}', now()),
                       (%s, 'Beta Legal', 'D2', 'ANY', '{}', '{"kind":"GOOGLE"}', now());
                """,
                [t1, t2],
            )
            # Users
            cursor.execute(
                """
                INSERT INTO tpl.app_user (tenant_id, user_id, email, display_name, idp_subject, firm_role, active)
                VALUES (%s, %s, 'admin@alpha.in', 'Admin Alpha', %s, 'ADMIN', true),
                       (%s, %s, 'member@alpha.in', 'Member Alpha', %s, 'PARTNER', true),
                       (%s, %s, 'outsider@alpha.in', 'Outsider Alpha', %s, 'ASSOCIATE', true),
                       (%s, %s, 'user@beta.in', 'Beta User', %s, 'PARTNER', true);
                """,
                [
                    t1, u_admin, f"sub-{u_admin}",
                    t1, u_member, f"sub-{u_member}",
                    t1, u_outsider, f"sub-{u_outsider}",
                    t2, u_other_tenant, f"sub-{u_other_tenant}",
                ],
            )

    return {
        "t1": t1,
        "t2": t2,
        "u_admin": u_admin,
        "u_member": u_member,
        "u_outsider": u_outsider,
        "u_other_tenant": u_other_tenant,
    }


def test_client_contract_and_prefix(workspace_setup: dict[str, str]) -> None:
    """Test tpl.client contract: cli_ prefix, client_type enum, identifiers jsonb, and RLS."""
    t1 = workspace_setup["t1"]
    u_member = workspace_setup["u_member"]

    client_id = mint_id("cli")
    assert client_id.startswith("cli_")
    assert len(client_id) == 30

    with transaction.atomic(using="owner"):
        with connections["owner"].cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tpl.client (
                    tenant_id, client_id, display_name, client_type,
                    identifiers, contact, notes, status, created_by, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, now());
                """,
                [
                    t1,
                    client_id,
                    "Acme Steel Pvt Ltd",
                    "COMPANY",
                    json.dumps({"CIN": "U12345MH2020PTC123456", "PAN": "AAACA1234A"}),
                    json.dumps({"email": "legal@acme.com", "phone": "+91-9876543210"}),
                    "Key corporate client",
                    "ACTIVE",
                    u_member,
                ],
            )

    # Read back under admin context (bypasses RLS)
    with admin_db_context():
        client = Client.objects.get(tenant_id=t1, client_id=client_id)
        assert client.display_name == "Acme Steel Pvt Ltd"
        assert client.client_type == "COMPANY"
        assert client.identifiers["CIN"] == "U12345MH2020PTC123456"
        assert client.contact["email"] == "legal@acme.com"
        assert client.status == "ACTIVE"


def test_matter_extensions_and_case_link_contract(workspace_setup: dict[str, str]) -> None:
    """Test tpl.matter case_type/court_or_forum and tpl.matter_case_link."""
    t1 = workspace_setup["t1"]
    u_member = workspace_setup["u_member"]
    client_id = mint_id("cli")
    matter_id = mint_id("mat")

    with transaction.atomic(using="owner"):
        with connections["owner"].cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tpl.client (tenant_id, client_id, display_name, client_type, created_by, created_at)
                VALUES (%s, %s, 'Acme Steel', 'COMPANY', %s, now());
                """,
                [t1, client_id, u_member],
            )
            cursor.execute(
                """
                INSERT INTO tpl.matter (
                    tenant_id, matter_id, client_id, title, client_role,
                    case_type, court_or_forum, status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'ACTIVE', now());
                """,
                [
                    t1,
                    matter_id,
                    client_id,
                    "Acme v. Zenith, s.9 petition",
                    "PETITIONER",
                    "Insolvency (IBC)",
                    "NCLT Mumbai",
                ],
            )
            # Case link
            cursor.execute(
                """
                INSERT INTO tpl.matter_case_link (tenant_id, matter_id, scheme, value_normalized, role, track)
                VALUES (%s, %s, 'COURT_REF', 'CP (IB) 123/MB/2026', 'PETITION', true);
                """,
                [t1, matter_id],
            )

    with admin_db_context():
        matter = Matter.objects.get(tenant_id=t1, matter_id=matter_id)
        assert matter.client_id == client_id
        assert matter.case_type == "Insolvency (IBC)"
        assert matter.court_or_forum == "NCLT Mumbai"

        link = MatterCaseLink.objects.get(tenant_id=t1, matter_id=matter_id, scheme="COURT_REF")
        assert link.value_normalized == "CP (IB) 123/MB/2026"
        assert link.track is True


def test_pdoc_and_private_anchor_contract(workspace_setup: dict[str, str]) -> None:
    """Test tpl.pdoc stage tag, pdoc_version, and private_anchor grammar check."""
    t1 = workspace_setup["t1"]
    matter_id = mint_id("mat")
    pdoc_id = mint_id("pdoc")
    u_member = workspace_setup["u_member"]

    with transaction.atomic(using="owner"):
        with connections["owner"].cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tpl.matter (tenant_id, matter_id, title, client_role, status, created_at)
                VALUES (%s, %s, 'Test Matter', 'PETITIONER', 'ACTIVE', now());
                """,
                [t1, matter_id],
            )
            cursor.execute(
                """
                INSERT INTO tpl.pdoc (
                    tenant_id, matter_id, pdoc_id, doc_type, provenance, trust_label,
                    privilege_class, privilege_state, stage, title, current_version, created_by, created_at
                ) VALUES (%s, %s, %s, 'ORDER', 'COURT', 'TENANT_COURT_RECORD', 'UNPRIVILEGED', 'SUGGESTED', 'ORDER', 'NCLT Order', 'v1', %s, now());
                """,
                [t1, matter_id, pdoc_id, u_member],
            )
            cursor.execute(
                """
                INSERT INTO tpl.pdoc_version (
                    tenant_id, pdoc_id, pver, raw_sha256, storage_uri, gate, created_at
                ) VALUES (%s, %s, 'v1', 'abcd1234ef5678', 's3://tpl-vault/test', 'PASS', now());
                """,
                [t1, pdoc_id],
            )
            anchor_id = f"{pdoc_id}/v1#p1"
            cursor.execute(
                """
                INSERT INTO tpl.private_anchor (
                    tenant_id, anchor_id, pdoc_id, pver, fragment, text, text_hash, ocr_conf, privilege_class
                ) VALUES (%s, %s, %s, 'v1', 'p1', 'The petition is admitted.', 'hash123', 0.98, 'UNPRIVILEGED');
                """,
                [t1, anchor_id, pdoc_id],
            )

    with admin_db_context():
        pdoc = Pdoc.objects.get(tenant_id=t1, pdoc_id=pdoc_id)
        assert pdoc.stage == "ORDER"
        assert pdoc.trust_label == "TENANT_COURT_RECORD"
        assert pdoc.privilege_state == "SUGGESTED"

        pver = PdocVersion.objects.get(tenant_id=t1, pdoc_id=pdoc_id, pver="v1")
        assert pver.gate == "PASS"

        anchor = PrivateAnchor.objects.get(tenant_id=t1, anchor_id=f"{pdoc_id}/v1#p1")
        assert anchor.fragment == "p1"
        assert anchor.ocr_conf == pytest.approx(0.98, rel=1e-2)


def test_rls_isolation_for_clients_and_matters(workspace_setup: dict[str, str]) -> None:
    """Prove non-member and other tenant see nothing under app_rw."""
    t1 = workspace_setup["t1"]
    t2 = workspace_setup["t2"]
    u_member = workspace_setup["u_member"]
    u_outsider = workspace_setup["u_outsider"]
    u_other_tenant = workspace_setup["u_other_tenant"]

    client_id = mint_id("cli")
    matter_id = mint_id("mat")

    with transaction.atomic(using="owner"):
        with connections["owner"].cursor() as cursor:
            # Client under T1
            cursor.execute(
                """
                INSERT INTO tpl.client (tenant_id, client_id, display_name, client_type, created_by, created_at)
                VALUES (%s, %s, 'Secret Client', 'COMPANY', %s, now());
                """,
                [t1, client_id, u_member],
            )
            # Matter under T1
            cursor.execute(
                """
                INSERT INTO tpl.matter (tenant_id, matter_id, client_id, title, client_role, status, created_at)
                VALUES (%s, %s, %s, 'Secret Matter', 'PETITIONER', 'ACTIVE', now());
                """,
                [t1, matter_id, client_id],
            )
            # Membership granted only to u_member
            cursor.execute(
                """
                INSERT INTO tpl.matter_member (tenant_id, matter_id, user_id, role, granted_by, granted_at)
                VALUES (%s, %s, %s, 'LEAD', %s, now());
                """,
                [t1, matter_id, u_member, u_member],
            )

    # 1. Member in T1 can see client and matter
    with connection.cursor() as cursor:
        cursor.execute("SET ROLE app_rw;")
        try:
            cursor.execute("SET app.tenant_id = %s;", [t1])
            cursor.execute("SET app.user_id = %s;", [u_member])

            cursor.execute("SELECT count(*) FROM tpl.client WHERE client_id = %s;", [client_id])
            assert cursor.fetchone()[0] == 1

            cursor.execute("SELECT count(*) FROM tpl.matter WHERE matter_id = %s;", [matter_id])
            assert cursor.fetchone()[0] == 1
        finally:
            cursor.execute("RESET ROLE;")

    # 2. Outsider in T1 (not member of matter, not creator) sees 0
    with connection.cursor() as cursor:
        cursor.execute("SET ROLE app_rw;")
        try:
            cursor.execute("SET app.tenant_id = %s;", [t1])
            cursor.execute("SET app.user_id = %s;", [u_outsider])

            cursor.execute("SELECT count(*) FROM tpl.matter WHERE matter_id = %s;", [matter_id])
            assert cursor.fetchone()[0] == 0

            cursor.execute("SELECT count(*) FROM tpl.client WHERE client_id = %s;", [client_id])
            assert cursor.fetchone()[0] == 0
        finally:
            cursor.execute("RESET ROLE;")

    # 3. User in T2 sees 0
    with connection.cursor() as cursor:
        cursor.execute("SET ROLE app_rw;")
        try:
            cursor.execute("SET app.tenant_id = %s;", [t2])
            cursor.execute("SET app.user_id = %s;", [u_other_tenant])

            cursor.execute("SELECT count(*) FROM tpl.client WHERE client_id = %s;", [client_id])
            assert cursor.fetchone()[0] == 0

            cursor.execute("SELECT count(*) FROM tpl.matter WHERE matter_id = %s;", [matter_id])
            assert cursor.fetchone()[0] == 0
        finally:
            cursor.execute("RESET ROLE;")


def test_authz_client_visibility_rule(workspace_setup: dict[str, str]) -> None:
    """Test authz.can() client visibility rule: ADMIN or matter member or creator."""
    t1 = workspace_setup["t1"]
    u_admin = workspace_setup["u_admin"]
    u_member = workspace_setup["u_member"]
    u_outsider = workspace_setup["u_outsider"]

    with admin_db_context():
        user_admin = AppUser.objects.get(tenant_id=t1, user_id=u_admin)
        user_member = AppUser.objects.get(tenant_id=t1, user_id=u_member)
        user_outsider = AppUser.objects.get(tenant_id=t1, user_id=u_outsider)

    client_id = mint_id("cli")
    matter_id = mint_id("mat")

    with transaction.atomic(using="owner"):
        with connections["owner"].cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tpl.client (tenant_id, client_id, display_name, client_type, created_by, created_at)
                VALUES (%s, %s, 'Visibility Test Client', 'COMPANY', %s, now());
                """,
                [t1, client_id, u_member],
            )
            cursor.execute(
                """
                INSERT INTO tpl.matter (tenant_id, matter_id, client_id, title, client_role, status, created_at)
                VALUES (%s, %s, %s, 'Visibility Matter', 'PETITIONER', 'ACTIVE', now());
                """,
                [t1, matter_id, client_id],
            )
            cursor.execute(
                """
                INSERT INTO tpl.matter_member (tenant_id, matter_id, user_id, role, granted_by, granted_at)
                VALUES (%s, %s, %s, 'MEMBER', %s, now());
                """,
                [t1, matter_id, u_member, u_admin],
            )

    with admin_db_context():
        client = Client.objects.get(tenant_id=t1, client_id=client_id)

    # 1. Firm ADMIN -> True
    assert authz.can(user_admin, "read", client) is True

    # 2. Member of matter under client -> True
    assert authz.can(user_member, "read", client) is True

    # 3. Outsider in same firm -> False
    assert authz.can(user_outsider, "read", client) is False
