"""Ninja Router for Client File, Matters, and Document Vault (Surface P10/P7).

Normative sources:
- Session R1: the client file (clients, matters, document vault)
- docs/mvp/00_mvp_spec.md §4.1, §4.3
- docs/mvp/03_data_model_and_contracts.md §3.8, §3.9, §6
- docs/12_P10_product_surface.md §2.1
- DECISIONS.md (2026-10-17 Session R1)
"""

from __future__ import annotations

import json
from typing import Any

from django.db import connection, transaction
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from ninja import File, Form, Router, Schema, UploadedFile
from ninja.errors import HttpError

from anchor_lib.ids import mint_id
from core.authz_dependency import authz_required
from parse.vault import DocumentVaultService, VaultStorage
from workspace import authz
from workspace.audit import record_audit_event
from workspace.db import tenant_db_context
from workspace.models import (
    AppUser,
    Client,
    Matter,
    MatterCaseLink,
    Pdoc,
    PdocVersion,
    PrivateAnchor,
)

router = Router(tags=["Clients, Matters & Vault"], auth=authz_required)


# ==============================================================================
# Schemas
# ==============================================================================


class ClientCreateRequest(Schema):
    display_name: str
    client_type: str = "COMPANY"
    identifiers: dict[str, Any] = {}
    contact: dict[str, Any] = {}
    notes: str | None = None


class ClientUpdateRequest(Schema):
    display_name: str | None = None
    client_type: str | None = None
    identifiers: dict[str, Any] | None = None
    contact: dict[str, Any] | None = None
    notes: str | None = None
    status: str | None = None


class ClientResponse(Schema):
    client_id: str
    display_name: str
    client_type: str
    identifiers: dict[str, Any]
    contact: dict[str, Any]
    notes: str | None
    status: str
    created_by: str
    created_at: str


class MatterSummaryResponse(Schema):
    matter_id: str
    client_id: str | None
    title: str
    client_role: str
    case_type: str | None
    court_or_forum: str | None
    status: str
    created_at: str


class ClientDetailResponse(Schema):
    client: ClientResponse
    matters: list[MatterSummaryResponse]


class MatterCreateRequest(Schema):
    client_id: str
    title: str
    client_role: str = "PETITIONER"
    case_type: str | None = None
    court_or_forum: str | None = None
    client_matter_no: str | None = None
    jurisdiction_state: str | None = None
    walled: bool = False


class MatterUpdateRequest(Schema):
    title: str | None = None
    client_role: str | None = None
    case_type: str | None = None
    court_or_forum: str | None = None
    client_matter_no: str | None = None
    jurisdiction_state: str | None = None
    status: str | None = None


class CaseLinkResponse(Schema):
    matter_id: str
    scheme: str
    value_normalized: str
    role: str
    track: bool


class CaseLinkCreateRequest(Schema):
    scheme: str
    value_normalized: str
    role: str = "CASE"
    track: bool = True


class PdocResponse(Schema):
    pdoc_id: str
    matter_id: str
    family_id: str | None
    parent_pdoc_id: str | None
    doc_type: str
    provenance: str
    trust_label: str
    privilege_class: str
    privilege_state: str
    stage: str
    title: str | None
    current_version: str | None
    created_by: str
    created_at: str


class PdocVersionResponse(Schema):
    pdoc_id: str
    pver: str
    raw_sha256: str
    storage_uri: str
    mime: str | None
    gate: str | None
    created_at: str


class PrivateAnchorItem(Schema):
    anchor_id: str
    fragment: str
    text: str
    ocr_conf: float | None
    privilege_class: str


class ParagraphViewResponse(Schema):
    pdoc_id: str
    pver: str
    title: str | None
    doc_type: str
    stage: str
    paragraphs: list[PrivateAnchorItem]


class MatterDetailResponse(Schema):
    matter: MatterSummaryResponse
    client: ClientResponse | None
    case_links: list[CaseLinkResponse]
    documents_count: int


# ==============================================================================
# Helper
# ==============================================================================


def _get_app_user(request: HttpRequest) -> AppUser:
    user = getattr(request, "app_user", None)
    if not isinstance(user, AppUser):
        raise HttpError(401, "Authenticated AppUser required.")
    return user


# ==============================================================================
# Client Endpoints
# ==============================================================================


@router.get("/clients", response=list[ClientResponse], auth=authz_required)
def list_clients(request: HttpRequest) -> list[dict[str, Any]]:
    """List clients visible to the user under RLS and can_read_client rule."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        clients = Client.objects.filter(tenant_id=user.tenant_id).order_by("-created_at")
        results: list[dict[str, Any]] = []
        for c in clients:
            if authz.can(user, "read", c):
                results.append(
                    {
                        "client_id": c.client_id,
                        "display_name": c.display_name,
                        "client_type": c.client_type,
                        "identifiers": c.identifiers or {},
                        "contact": c.contact or {},
                        "notes": c.notes,
                        "status": c.status,
                        "created_by": c.created_by,
                        "created_at": c.created_at.isoformat(),
                    }
                )
        return results


@router.post("/clients", response=ClientResponse, auth=authz_required)
def create_client(request: HttpRequest, payload: ClientCreateRequest) -> dict[str, Any]:
    """Create a new client entity."""
    user = _get_app_user(request)
    client_id = mint_id("cli")
    now = timezone.now()

    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tpl.client (
                        tenant_id, client_id, display_name, client_type,
                        identifiers, contact, notes, status, created_by, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'ACTIVE', %s, %s)
                    """,
                    [
                        user.tenant_id,
                        client_id,
                        payload.display_name,
                        payload.client_type,
                        json.dumps(payload.identifiers),
                        json.dumps(payload.contact),
                        payload.notes,
                        user.user_id,
                        now,
                    ],
                )

            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user.user_id,
                action="CLIENT_CREATE",
                object_ref=client_id,
                decision="ALLOW",
                detail={"display_name": payload.display_name, "client_type": payload.client_type},
            )

    return {
        "client_id": client_id,
        "display_name": payload.display_name,
        "client_type": payload.client_type,
        "identifiers": payload.identifiers,
        "contact": payload.contact,
        "notes": payload.notes,
        "status": "ACTIVE",
        "created_by": user.user_id,
        "created_at": now.isoformat(),
    }


@router.get("/clients/{client_id}", response=ClientDetailResponse, auth=authz_required)
def get_client(request: HttpRequest, client_id: str) -> dict[str, Any]:
    """Get client details and its matters."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        client = Client.objects.filter(tenant_id=user.tenant_id, client_id=client_id).first()
        if not client or not authz.can(user, "read", client):
            raise HttpError(403, "Access to this client is forbidden.")

        matters = Matter.objects.filter(tenant_id=user.tenant_id, client_id=client_id).order_by(
            "-created_at"
        )
        accessible_matters: list[dict[str, Any]] = []
        for m in matters:
            if authz.can(user, "read", m):
                accessible_matters.append(
                    {
                        "matter_id": m.matter_id,
                        "client_id": m.client_id,
                        "title": m.title,
                        "client_role": m.client_role,
                        "case_type": m.case_type,
                        "court_or_forum": m.court_or_forum,
                        "status": m.status,
                        "created_at": m.created_at.isoformat(),
                    }
                )

        record_audit_event(
            tenant_id=user.tenant_id,
            actor=user.user_id,
            action="CLIENT_VIEW",
            object_ref=client_id,
            decision="ALLOW",
        )

        return {
            "client": {
                "client_id": client.client_id,
                "display_name": client.display_name,
                "client_type": client.client_type,
                "identifiers": client.identifiers or {},
                "contact": client.contact or {},
                "notes": client.notes,
                "status": client.status,
                "created_by": client.created_by,
                "created_at": client.created_at.isoformat(),
            },
            "matters": accessible_matters,
        }


@router.patch("/clients/{client_id}", response=ClientResponse, auth=authz_required)
def update_client(
    request: HttpRequest, client_id: str, payload: ClientUpdateRequest
) -> dict[str, Any]:
    """Update client fields."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        client = Client.objects.filter(tenant_id=user.tenant_id, client_id=client_id).first()
        if not client or not authz.can(user, "update", client):
            raise HttpError(403, "Access to update this client is forbidden.")

        updates: list[str] = []
        params: list[Any] = []
        if payload.display_name is not None:
            updates.append("display_name = %s")
            params.append(payload.display_name)
        if payload.client_type is not None:
            updates.append("client_type = %s")
            params.append(payload.client_type)
        if payload.identifiers is not None:
            updates.append("identifiers = %s")
            params.append(json.dumps(payload.identifiers))
        if payload.contact is not None:
            updates.append("contact = %s")
            params.append(json.dumps(payload.contact))
        if payload.notes is not None:
            updates.append("notes = %s")
            params.append(payload.notes)
        if payload.status is not None:
            updates.append("status = %s")
            params.append(payload.status)

        if updates:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    sql = f"UPDATE tpl.client SET {', '.join(updates)} WHERE tenant_id = %s AND client_id = %s"
                    cursor.execute(sql, [*params, user.tenant_id, client_id])

                record_audit_event(
                    tenant_id=user.tenant_id,
                    actor=user.user_id,
                    action="CLIENT_UPDATE",
                    object_ref=client_id,
                    decision="ALLOW",
                    detail={"updated_fields": list(payload.dict(exclude_unset=True).keys())},
                )

        updated = Client.objects.get(tenant_id=user.tenant_id, client_id=client_id)
        return {
            "client_id": updated.client_id,
            "display_name": updated.display_name,
            "client_type": updated.client_type,
            "identifiers": updated.identifiers or {},
            "contact": updated.contact or {},
            "notes": updated.notes,
            "status": updated.status,
            "created_by": updated.created_by,
            "created_at": updated.created_at.isoformat(),
        }


@router.post("/clients/{client_id}/archive", response=ClientResponse, auth=authz_required)
def archive_client(request: HttpRequest, client_id: str) -> dict[str, Any]:
    """Archive client."""
    return update_client(request, client_id, ClientUpdateRequest(status="ARCHIVED"))


# ==============================================================================
# Matter Endpoints
# ==============================================================================


@router.get("/clients/{client_id}/matters", response=list[MatterSummaryResponse], auth=authz_required)
def list_client_matters(request: HttpRequest, client_id: str) -> list[dict[str, Any]]:
    """List matters opened under a client."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        client = Client.objects.filter(tenant_id=user.tenant_id, client_id=client_id).first()
        if not client or not authz.can(user, "read", client):
            raise HttpError(403, "Access to this client is forbidden.")

        matters = Matter.objects.filter(tenant_id=user.tenant_id, client_id=client_id).order_by(
            "-created_at"
        )
        return [
            {
                "matter_id": m.matter_id,
                "client_id": m.client_id,
                "title": m.title,
                "client_role": m.client_role,
                "case_type": m.case_type,
                "court_or_forum": m.court_or_forum,
                "status": m.status,
                "created_at": m.created_at.isoformat(),
            }
            for m in matters
            if authz.can(user, "read", m)
        ]


@router.get("/matters", response=list[MatterSummaryResponse], auth=authz_required)
def list_all_matters(request: HttpRequest) -> list[dict[str, Any]]:
    """List all matters accessible to user."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matters = Matter.objects.filter(tenant_id=user.tenant_id).order_by("-created_at")
        return [
            {
                "matter_id": m.matter_id,
                "client_id": m.client_id,
                "title": m.title,
                "client_role": m.client_role,
                "case_type": m.case_type,
                "court_or_forum": m.court_or_forum,
                "status": m.status,
                "created_at": m.created_at.isoformat(),
            }
            for m in matters
            if authz.can(user, "read", m)
        ]


@router.post("/matters", response=MatterSummaryResponse, auth=authz_required)
def create_matter(request: HttpRequest, payload: MatterCreateRequest) -> dict[str, Any]:
    """Open a new matter under a client."""
    user = _get_app_user(request)
    if not payload.client_id:
        raise HttpError(400, "client_id is required for all new matters.")

    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        client = Client.objects.filter(tenant_id=user.tenant_id, client_id=payload.client_id).first()
        if not client or not authz.can(user, "read", client):
            raise HttpError(403, "Access to client forbidden.")

        matter_id = mint_id("mat")
        now = timezone.now()

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tpl.matter (
                        tenant_id, matter_id, client_id, client_matter_no, title,
                        client_role, case_type, court_or_forum, jurisdiction_state,
                        status, walled, legal_hold, context_version, membership_version,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE', %s, false, 0, 1, %s)
                    """,
                    [
                        user.tenant_id,
                        matter_id,
                        payload.client_id,
                        payload.client_matter_no,
                        payload.title,
                        payload.client_role,
                        payload.case_type,
                        payload.court_or_forum,
                        payload.jurisdiction_state,
                        payload.walled,
                        now,
                    ],
                )

                # Creator is added as LEAD member
                cursor.execute(
                    """
                    INSERT INTO tpl.matter_member (
                        tenant_id, matter_id, user_id, role, granted_by, granted_at
                    ) VALUES (%s, %s, %s, 'LEAD', %s, %s)
                    """,
                    [user.tenant_id, matter_id, user.user_id, user.user_id, now],
                )

            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user.user_id,
                action="MATTER_CREATE",
                object_ref=matter_id,
                matter_id=matter_id,
                decision="ALLOW",
                detail={
                    "client_id": payload.client_id,
                    "title": payload.title,
                    "case_type": payload.case_type,
                    "court": payload.court_or_forum,
                },
            )

    return {
        "matter_id": matter_id,
        "client_id": payload.client_id,
        "title": payload.title,
        "client_role": payload.client_role,
        "case_type": payload.case_type,
        "court_or_forum": payload.court_or_forum,
        "status": "ACTIVE",
        "created_at": now.isoformat(),
    }


@router.get("/matters/{matter_id}", response=MatterDetailResponse, auth=authz_required)
def get_matter(request: HttpRequest, matter_id: str) -> dict[str, Any]:
    """Get full details of a matter including client, case links, and document count."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "read", matter):
            raise HttpError(403, "Access to this matter is forbidden.")

        client_resp: dict[str, Any] | None = None
        if matter.client_id:
            c = Client.objects.filter(tenant_id=user.tenant_id, client_id=matter.client_id).first()
            if c and authz.can(user, "read", c):
                client_resp = {
                    "client_id": c.client_id,
                    "display_name": c.display_name,
                    "client_type": c.client_type,
                    "identifiers": c.identifiers or {},
                    "contact": c.contact or {},
                    "notes": c.notes,
                    "status": c.status,
                    "created_by": c.created_by,
                    "created_at": c.created_at.isoformat(),
                }

        case_links = MatterCaseLink.objects.filter(
            tenant_id=user.tenant_id, matter_id=matter_id
        ).order_by("scheme", "value_normalized")
        docs_count = Pdoc.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).count()

        record_audit_event(
            tenant_id=user.tenant_id,
            actor=user.user_id,
            action="MATTER_VIEW",
            object_ref=matter_id,
            matter_id=matter_id,
            decision="ALLOW",
        )

        return {
            "matter": {
                "matter_id": matter.matter_id,
                "client_id": matter.client_id,
                "title": matter.title,
                "client_role": matter.client_role,
                "case_type": matter.case_type,
                "court_or_forum": matter.court_or_forum,
                "status": matter.status,
                "created_at": matter.created_at.isoformat(),
            },
            "client": client_resp,
            "case_links": [
                {
                    "matter_id": cl.matter_id,
                    "scheme": cl.scheme,
                    "value_normalized": cl.value_normalized,
                    "role": cl.role,
                    "track": cl.track,
                }
                for cl in case_links
            ],
            "documents_count": docs_count,
        }


@router.patch("/matters/{matter_id}", response=MatterSummaryResponse, auth=authz_required)
def update_matter(
    request: HttpRequest, matter_id: str, payload: MatterUpdateRequest
) -> dict[str, Any]:
    """Update matter properties."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "update", matter):
            raise HttpError(403, "Access to update this matter is forbidden.")

        updates: list[str] = []
        params: list[Any] = []
        if payload.title is not None:
            updates.append("title = %s")
            params.append(payload.title)
        if payload.client_role is not None:
            updates.append("client_role = %s")
            params.append(payload.client_role)
        if payload.case_type is not None:
            updates.append("case_type = %s")
            params.append(payload.case_type)
        if payload.court_or_forum is not None:
            updates.append("court_or_forum = %s")
            params.append(payload.court_or_forum)
        if payload.client_matter_no is not None:
            updates.append("client_matter_no = %s")
            params.append(payload.client_matter_no)
        if payload.jurisdiction_state is not None:
            updates.append("jurisdiction_state = %s")
            params.append(payload.jurisdiction_state)
        if payload.status is not None:
            updates.append("status = %s")
            params.append(payload.status)

        if updates:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    sql = f"UPDATE tpl.matter SET {', '.join(updates)} WHERE tenant_id = %s AND matter_id = %s"
                    cursor.execute(sql, [*params, user.tenant_id, matter_id])

                record_audit_event(
                    tenant_id=user.tenant_id,
                    actor=user.user_id,
                    action="MATTER_UPDATE",
                    object_ref=matter_id,
                    matter_id=matter_id,
                    decision="ALLOW",
                    detail={"updated_fields": list(payload.dict(exclude_unset=True).keys())},
                )

        updated = Matter.objects.get(tenant_id=user.tenant_id, matter_id=matter_id)
        return {
            "matter_id": updated.matter_id,
            "client_id": updated.client_id,
            "title": updated.title,
            "client_role": updated.client_role,
            "case_type": updated.case_type,
            "court_or_forum": updated.court_or_forum,
            "status": updated.status,
            "created_at": updated.created_at.isoformat(),
        }


@router.post("/matters/{matter_id}/close", response=MatterSummaryResponse, auth=authz_required)
def close_matter(request: HttpRequest, matter_id: str) -> dict[str, Any]:
    """Close matter."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "update", matter):
            raise HttpError(403, "Access to close this matter is forbidden.")

        now = timezone.now()
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE tpl.matter
                    SET status = 'CLOSED', closed_at = %s
                    WHERE tenant_id = %s AND matter_id = %s
                    """,
                    [now, user.tenant_id, matter_id],
                )

            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user.user_id,
                action="MATTER_CLOSE",
                object_ref=matter_id,
                matter_id=matter_id,
                decision="ALLOW",
            )

        updated = Matter.objects.get(tenant_id=user.tenant_id, matter_id=matter_id)
        return {
            "matter_id": updated.matter_id,
            "client_id": updated.client_id,
            "title": updated.title,
            "client_role": updated.client_role,
            "case_type": updated.case_type,
            "court_or_forum": updated.court_or_forum,
            "status": updated.status,
            "created_at": updated.created_at.isoformat(),
        }


# ==============================================================================
# Case Links
# ==============================================================================


@router.get("/matters/{matter_id}/case-links", response=list[CaseLinkResponse], auth=authz_required)
def list_case_links(request: HttpRequest, matter_id: str) -> list[dict[str, Any]]:
    """List case numbers associated with a matter."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "read", matter):
            raise HttpError(403, "Access to this matter is forbidden.")

        links = MatterCaseLink.objects.filter(
            tenant_id=user.tenant_id, matter_id=matter_id
        ).order_by("scheme", "value_normalized")
        return [
            {
                "matter_id": cl.matter_id,
                "scheme": cl.scheme,
                "value_normalized": cl.value_normalized,
                "role": cl.role,
                "track": cl.track,
            }
            for cl in links
        ]


@router.post("/matters/{matter_id}/case-links", response=CaseLinkResponse, auth=authz_required)
def add_case_link(
    request: HttpRequest, matter_id: str, payload: CaseLinkCreateRequest
) -> dict[str, Any]:
    """Add a case number link to a matter."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "write", matter):
            raise HttpError(403, "Access to modify this matter is forbidden.")

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tpl.matter_case_link (
                        tenant_id, matter_id, scheme, value_normalized, role, track
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tenant_id, matter_id, scheme, value_normalized)
                    DO UPDATE SET role = EXCLUDED.role, track = EXCLUDED.track
                    """,
                    [
                        user.tenant_id,
                        matter_id,
                        payload.scheme,
                        payload.value_normalized,
                        payload.role,
                        payload.track,
                    ],
                )

            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user.user_id,
                action="CASE_LINK_ADD",
                object_ref=f"{payload.scheme}:{payload.value_normalized}",
                matter_id=matter_id,
                decision="ALLOW",
                detail={"scheme": payload.scheme, "value": payload.value_normalized},
            )

        return {
            "matter_id": matter_id,
            "scheme": payload.scheme,
            "value_normalized": payload.value_normalized,
            "role": payload.role,
            "track": payload.track,
        }


@router.delete("/matters/{matter_id}/case-links", auth=authz_required)
def remove_case_link(
    request: HttpRequest, matter_id: str, scheme: str, value_normalized: str
) -> dict[str, Any]:
    """Remove a case number link from a matter."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "write", matter):
            raise HttpError(403, "Access to modify this matter is forbidden.")

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM tpl.matter_case_link
                    WHERE tenant_id = %s AND matter_id = %s AND scheme = %s AND value_normalized = %s
                    """,
                    [user.tenant_id, matter_id, scheme, value_normalized],
                )

            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user.user_id,
                action="CASE_LINK_REMOVE",
                object_ref=f"{scheme}:{value_normalized}",
                matter_id=matter_id,
                decision="ALLOW",
            )

    return {"status": "ok", "removed": f"{scheme}:{value_normalized}"}


# ==============================================================================
# Document Vault Endpoints
# ==============================================================================


@router.post("/matters/{matter_id}/documents/upload", response=list[PdocResponse], auth=authz_required)
def upload_document(
    request: HttpRequest,
    matter_id: str,
    file: File[UploadedFile],
    doc_type: Form[str] = "OTHER",
    provenance: Form[str] = "CLIENT",
    trust_label: Form[str] = "TENANT_CLIENT_DOC",
    stage: Form[str] = "OTHER",
    privilege_class: Form[str] = "ATTORNEY_CLIENT",
    pdoc_id: Form[str | None] = None,
    title: Form[str | None] = None,
) -> list[dict[str, Any]]:
    """Upload and parse a document (PDF, DOCX, EML, ZIP) into the matter vault."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "upload", matter):
            raise HttpError(403, "Access to upload documents to this matter is forbidden.")

    raw_bytes = file.read()
    vault = DocumentVaultService()
    try:
        pdocs = vault.ingest(
            tenant_id=user.tenant_id,
            matter_id=matter_id,
            user_id=user.user_id,
            filename=file.name or "uploaded_file",
            raw_bytes=raw_bytes,
            doc_type=doc_type,
            provenance=provenance,
            trust_label=trust_label,
            privilege_class=privilege_class,
            stage=stage,
            title=title or file.name,
            pdoc_id=pdoc_id,
        )
    except ValueError as e:
        raise HttpError(400, str(e)) from e

    return [
        {
            "pdoc_id": p.pdoc_id,
            "matter_id": p.matter_id,
            "family_id": p.family_id,
            "parent_pdoc_id": p.parent_pdoc_id,
            "doc_type": p.doc_type,
            "provenance": p.provenance,
            "trust_label": p.trust_label,
            "privilege_class": p.privilege_class,
            "privilege_state": p.privilege_state,
            "stage": p.stage,
            "title": p.title,
            "current_version": p.current_version,
            "created_by": p.created_by,
            "created_at": p.created_at.isoformat(),
        }
        for p in pdocs
    ]


@router.get("/matters/{matter_id}/documents", response=list[PdocResponse], auth=authz_required)
def list_matter_documents(request: HttpRequest, matter_id: str) -> list[dict[str, Any]]:
    """List documents for a matter."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "read", matter):
            raise HttpError(403, "Access to this matter is forbidden.")

        docs = Pdoc.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).order_by(
            "-created_at"
        )
        return [
            {
                "pdoc_id": p.pdoc_id,
                "matter_id": p.matter_id,
                "family_id": p.family_id,
                "parent_pdoc_id": p.parent_pdoc_id,
                "doc_type": p.doc_type,
                "provenance": p.provenance,
                "trust_label": p.trust_label,
                "privilege_class": p.privilege_class,
                "privilege_state": p.privilege_state,
                "stage": p.stage,
                "title": p.title,
                "current_version": p.current_version,
                "created_by": p.created_by,
                "created_at": p.created_at.isoformat(),
            }
            for p in docs
        ]


@router.get("/documents/{pdoc_id}/versions", response=list[PdocVersionResponse], auth=authz_required)
def list_document_versions(request: HttpRequest, pdoc_id: str) -> list[dict[str, Any]]:
    """List all versions of a document."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        pdoc = Pdoc.objects.filter(tenant_id=user.tenant_id, pdoc_id=pdoc_id).first()
        if not pdoc or not authz.can(user, "read", pdoc):
            raise HttpError(403, "Access to this document is forbidden.")

        versions = PdocVersion.objects.filter(
            tenant_id=user.tenant_id, pdoc_id=pdoc_id
        ).order_by("created_at")
        return [
            {
                "pdoc_id": v.pdoc_id,
                "pver": v.pver,
                "raw_sha256": v.raw_sha256,
                "storage_uri": v.storage_uri,
                "mime": v.mime,
                "gate": v.gate,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ]


@router.get("/documents/{pdoc_id}/paragraphs", response=ParagraphViewResponse, auth=authz_required)
def get_document_paragraphs(
    request: HttpRequest, pdoc_id: str, pver: str | None = None
) -> dict[str, Any]:
    """Get numbered paragraphs with private anchors and OCR confidence for viewer."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        pdoc = Pdoc.objects.filter(tenant_id=user.tenant_id, pdoc_id=pdoc_id).first()
        if not pdoc or not authz.can(user, "view", pdoc):
            raise HttpError(403, "Access to this document is forbidden.")

        ver = pver or pdoc.current_version or "v1"
        anchors = PrivateAnchor.objects.filter(
            tenant_id=user.tenant_id, pdoc_id=pdoc_id, pver=ver
        ).order_by("anchor_id")

        record_audit_event(
            tenant_id=user.tenant_id,
            actor=user.user_id,
            action="DOCUMENT_VIEW",
            object_ref=f"{pdoc_id}/{ver}",
            matter_id=pdoc.matter_id,
            decision="ALLOW",
        )

        return {
            "pdoc_id": pdoc.pdoc_id,
            "pver": ver,
            "title": pdoc.title,
            "doc_type": pdoc.doc_type,
            "stage": pdoc.stage,
            "paragraphs": [
                {
                    "anchor_id": a.anchor_id,
                    "fragment": a.fragment,
                    "text": a.text,
                    "ocr_conf": a.ocr_conf,
                    "privilege_class": a.privilege_class,
                }
                for a in anchors
            ],
        }


@router.get("/documents/{pdoc_id}/download", auth=authz_required)
def download_document(
    request: HttpRequest, pdoc_id: str, pver: str | None = None
) -> HttpResponse:
    """Download immutable raw document bytes."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        pdoc = Pdoc.objects.filter(tenant_id=user.tenant_id, pdoc_id=pdoc_id).first()
        if not pdoc or not authz.can(user, "download", pdoc):
            raise HttpError(403, "Access to download this document is forbidden.")

        ver = pver or pdoc.current_version or "v1"
        version_obj = PdocVersion.objects.filter(
            tenant_id=user.tenant_id, pdoc_id=pdoc_id, pver=ver
        ).first()
        if not version_obj:
            raise HttpError(404, "Requested document version not found.")

        storage = VaultStorage()
        raw_bytes = storage.get_raw(version_obj.storage_uri)

        record_audit_event(
            tenant_id=user.tenant_id,
            actor=user.user_id,
            action="DOCUMENT_DOWNLOAD",
            object_ref=f"{pdoc_id}/{ver}",
            matter_id=pdoc.matter_id,
            decision="ALLOW",
            detail={"sha256": version_obj.raw_sha256, "mime": version_obj.mime},
        )

        filename = f"{pdoc.title or pdoc_id}_{ver}"
        mime = version_obj.mime or "application/octet-stream"
        response = HttpResponse(raw_bytes, content_type=mime)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
