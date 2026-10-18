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
from datetime import date, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from django.db import connection, transaction
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from ninja import File, Form, Router, Schema, UploadedFile
from ninja.errors import HttpError

from anchor_lib.case_numbers import normalize_case_number
from anchor_lib.ids import mint_id
from core.authz_dependency import authz_required
from parse.vault import DocumentVaultService, VaultStorage
from workspace import authz
from workspace.audit import record_audit_event
from workspace.db import tenant_db_context
from workspace.models import (
    AppUser,
    CaseCandidate,
    Client,
    Deadline,
    Hearing,
    Matter,
    MatterCaseLink,
    MatterDependency,
    Pdoc,
    PdocVersion,
    PrivateAnchor,
)

IST = ZoneInfo("Asia/Kolkata")

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
    parseable: bool = True
    warning: str | None = None


class CaseLinkCreateRequest(Schema):
    scheme: str
    value_normalized: str
    role: str = "CASE"
    track: bool = True


class HearingResponse(Schema):
    hearing_id: str
    matter_id: str
    date: str
    court_no: str | None
    item_no: str | None
    bench: str | None
    purpose: str | None
    source: str
    source_ref: str | None
    status: str
    outcome: str | None
    entered_by: str
    observed_at: str | None
    court_or_forum: str | None


class HearingCreateRequest(Schema):
    date: str
    court_no: str | None = None
    item_no: str | None = None
    bench: str | None = None
    purpose: str | None = None


class HearingOutcomeRequest(Schema):
    outcome: str
    status: str = "HEARD"
    next_date: str | None = None
    next_purpose: str | None = None


class DeadlineResponse(Schema):
    deadline_id: str
    matter_id: str
    rule_id: str | None
    label: str
    kind: str
    due_on: str
    lifecycle: str
    owner: str | None
    source_note: str
    created_at: str


class DeadlineCreateRequest(Schema):
    label: str
    due_on: str
    owner: str | None = None
    rule_id: str | None = None


class DeadlineLifecycleRequest(Schema):
    lifecycle: str


class CaseCandidateResponse(Schema):
    candidate_id: str
    matter_id: str
    kind: str
    source: str
    source_ref: str
    case_number_raw: str
    list_date: str | None
    bench: str | None
    normalized_case_no: str | None
    details: dict[str, Any]
    status: str
    created_at: str
    resolved_at: str | None
    resolved_by: str | None


class CourtOrderResponse(Schema):
    matter_id: str
    public_id: str
    match_key: str
    decision_date: str | None
    bench: str | None
    kind: str
    source_ref: str
    uncertified_badge: bool = True
    source_viewer_url: str


class TimelineItemResponse(Schema):
    id: str
    date: str
    item_type: str
    title: str
    subtitle: str | None
    status: str | None
    metadata: dict[str, Any]


class TodayHearingItem(Schema):
    hearing_id: str
    matter_id: str
    matter_title: str
    client_id: str | None
    court_or_forum: str | None
    court_no: str | None
    item_no: str | None
    bench: str | None
    purpose: str | None
    status: str
    date: str


class TodayDeadlineItem(Schema):
    deadline_id: str
    matter_id: str
    matter_title: str
    label: str
    due_on: str
    lifecycle: str
    source_note: str
    is_overdue: bool


class TodayResponse(Schema):
    today_date: str
    today_hearings: list[TodayHearingItem]
    tomorrow_hearings: list[TodayHearingItem]
    this_week_hearings: list[TodayHearingItem]
    this_week_deadlines: list[TodayDeadlineItem]
    pending_candidates: list[CaseCandidateResponse]
    recent_orders: list[CourtOrderResponse]
    total_active_matters: int


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
    """Add a case number link to a matter with normalization on write."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "write", matter):
            raise HttpError(403, "Access to modify this matter is forbidden.")

        parsed = normalize_case_number(payload.value_normalized)
        if parsed.parseable:
            val = parsed.canonical
            parseable = True
            warning = None
        else:
            val = payload.value_normalized.strip()
            parseable = False
            warning = "Case number format could not be parsed; automatic cause-list tracking will not run for this number until edited to a recognized format."

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
                        val,
                        payload.role,
                        payload.track,
                    ],
                )

            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user.user_id,
                action="CASE_LINK_ADD",
                object_ref=f"{payload.scheme}:{val}",
                matter_id=matter_id,
                decision="ALLOW",
                detail={
                    "scheme": payload.scheme,
                    "raw": payload.value_normalized,
                    "normalized": val,
                    "parseable": parseable,
                },
            )

        return {
            "matter_id": matter_id,
            "scheme": payload.scheme,
            "value_normalized": val,
            "role": payload.role,
            "track": payload.track,
            "parseable": parseable,
            "warning": warning,
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


# ==============================================================================
# R2: Hearings, Dates & Procedural Clock
# ==============================================================================


@router.get("/matters/{matter_id}/hearings", response=list[HearingResponse], auth=authz_required)
def list_matter_hearings(request: HttpRequest, matter_id: str) -> list[dict[str, Any]]:
    """List hearings for a matter."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "read", matter):
            raise HttpError(403, "Access to this matter is forbidden.")

        hearings = Hearing.objects.filter(
            tenant_id=user.tenant_id, matter_id=matter_id
        ).order_by("date", "court_no", "item_no")

        return [
            {
                "hearing_id": h.hearing_id,
                "matter_id": h.matter_id,
                "date": h.date.isoformat(),
                "court_no": h.court_no,
                "item_no": h.item_no,
                "bench": h.bench,
                "purpose": h.purpose,
                "source": h.source,
                "source_ref": h.source_ref,
                "status": h.status,
                "outcome": h.outcome,
                "entered_by": h.entered_by,
                "observed_at": h.observed_at.isoformat() if h.observed_at else None,
                "court_or_forum": (
                    h.bench
                    if (h.source == "CAUSE_LIST" and h.bench)
                    else (matter.court_or_forum or h.bench)
                ),
            }
            for h in hearings
        ]


@router.post("/matters/{matter_id}/hearings", response=HearingResponse, auth=authz_required)
def create_hearing(
    request: HttpRequest, matter_id: str, payload: HearingCreateRequest
) -> dict[str, Any]:
    """Manually enter a hearing for any court."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "write", matter):
            raise HttpError(403, "Access to modify this matter is forbidden.")

        hrg_id = mint_id("hrg")
        h_date = date.fromisoformat(payload.date)
        now = timezone.now()

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tpl.hearing (
                        tenant_id, matter_id, hearing_id, date, court_no, item_no,
                        bench, purpose, source, source_ref, status, outcome,
                        next_date, entered_by, observed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'MANUAL', NULL, 'LISTED', NULL, NULL, %s, %s)
                    """,
                    [
                        user.tenant_id,
                        matter_id,
                        hrg_id,
                        h_date,
                        payload.court_no,
                        payload.item_no,
                        payload.bench or matter.court_or_forum,
                        payload.purpose,
                        user.user_id,
                        now,
                    ],
                )

            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user.user_id,
                action="HEARING_CREATE",
                object_ref=hrg_id,
                matter_id=matter_id,
                decision="ALLOW",
                detail={"date": payload.date, "purpose": payload.purpose},
            )

        return {
            "hearing_id": hrg_id,
            "matter_id": matter_id,
            "date": h_date.isoformat(),
            "court_no": payload.court_no,
            "item_no": payload.item_no,
            "bench": payload.bench or matter.court_or_forum,
            "purpose": payload.purpose,
            "source": "MANUAL",
            "source_ref": None,
            "status": "LISTED",
            "outcome": None,
            "entered_by": user.user_id,
            "observed_at": now.isoformat(),
            "court_or_forum": matter.court_or_forum or payload.bench,
        }


@router.post("/hearings/{hearing_id}/outcome", response=HearingResponse, auth=authz_required)
def record_hearing_outcome(
    request: HttpRequest, hearing_id: str, payload: HearingOutcomeRequest
) -> dict[str, Any]:
    """Record outcome of a hearing and optionally schedule the next date in one click."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        hearing = Hearing.objects.filter(
            tenant_id=user.tenant_id, hearing_id=hearing_id
        ).first()
        if not hearing:
            raise HttpError(404, "Hearing not found.")

        matter = Matter.objects.filter(
            tenant_id=user.tenant_id, matter_id=hearing.matter_id
        ).first()
        if not matter or not authz.can(user, "write", matter):
            raise HttpError(403, "Access to modify this matter is forbidden.")

        now = timezone.now()
        next_d = date.fromisoformat(payload.next_date) if payload.next_date else None

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE tpl.hearing
                    SET outcome = %s, status = %s, next_date = %s
                    WHERE tenant_id = %s AND hearing_id = %s
                    """,
                    [payload.outcome, payload.status, next_d, user.tenant_id, hearing_id],
                )

                if next_d:
                    next_hrg_id = mint_id("hrg")
                    cursor.execute(
                        """
                        INSERT INTO tpl.hearing (
                            tenant_id, matter_id, hearing_id, date, court_no, item_no,
                            bench, purpose, source, source_ref, status, outcome,
                            next_date, entered_by, observed_at
                        ) VALUES (%s, %s, %s, %s, %s, NULL, %s, %s, 'MANUAL', NULL, 'LISTED', NULL, NULL, %s, %s)
                        """,
                        [
                            user.tenant_id,
                            hearing.matter_id,
                            next_hrg_id,
                            next_d,
                            hearing.court_no,
                            hearing.bench,
                            payload.next_purpose or "Next hearing",
                            user.user_id,
                            now,
                        ],
                    )

            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user.user_id,
                action="HEARING_OUTCOME",
                object_ref=hearing_id,
                matter_id=hearing.matter_id,
                decision="ALLOW",
                detail={
                    "outcome": payload.outcome,
                    "status": payload.status,
                    "next_date": payload.next_date,
                },
            )

        updated = Hearing.objects.get(tenant_id=user.tenant_id, hearing_id=hearing_id)
        return {
            "hearing_id": updated.hearing_id,
            "matter_id": updated.matter_id,
            "date": updated.date.isoformat(),
            "court_no": updated.court_no,
            "item_no": updated.item_no,
            "bench": updated.bench,
            "purpose": updated.purpose,
            "source": updated.source,
            "source_ref": updated.source_ref,
            "status": updated.status,
            "outcome": updated.outcome,
            "entered_by": updated.entered_by,
            "observed_at": updated.observed_at.isoformat() if updated.observed_at else None,
            "court_or_forum": (
                updated.bench
                if (updated.source == "CAUSE_LIST" and updated.bench)
                else (matter.court_or_forum or updated.bench)
            ),
        }


@router.get("/matters/{matter_id}/deadlines", response=list[DeadlineResponse], auth=authz_required)
def list_matter_deadlines(request: HttpRequest, matter_id: str) -> list[dict[str, Any]]:
    """List procedural deadlines and dates for a matter."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "read", matter):
            raise HttpError(403, "Access to this matter is forbidden.")

        deadlines = Deadline.objects.filter(
            tenant_id=user.tenant_id, matter_id=matter_id
        ).order_by("due_on")

        return [
            {
                "deadline_id": d.deadline_id,
                "matter_id": d.matter_id,
                "rule_id": d.rule_id,
                "label": d.label,
                "kind": d.kind,
                "due_on": d.due_on.isoformat(),
                "lifecycle": d.lifecycle,
                "owner": d.owner,
                "source_note": (
                    f"computed from {d.rule_id}"
                    if d.rule_id
                    else f"entered by {d.owner or 'lawyer'}, not computed"
                ),
                "created_at": d.created_at.isoformat(),
            }
            for d in deadlines
        ]


@router.post("/matters/{matter_id}/deadlines", response=DeadlineResponse, auth=authz_required)
def create_deadline(
    request: HttpRequest, matter_id: str, payload: DeadlineCreateRequest
) -> dict[str, Any]:
    """Manually enter a deadline or date. Rule-computed deadlines are rejected until R4."""
    user = _get_app_user(request)
    if payload.rule_id is not None:
        raise HttpError(400, "Rule-computed deadlines are disabled until Session R4.")

    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "write", matter):
            raise HttpError(403, "Access to modify this matter is forbidden.")

        ddl_id = mint_id("ddl")
        due_d = date.fromisoformat(payload.due_on)
        owner_name = payload.owner or user.user_id
        now = timezone.now()

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tpl.deadline (
                        tenant_id, matter_id, deadline_id, rule_id, rule_code,
                        rule_version, label, kind, due_on, status, lifecycle,
                        owner, statutory_anchors, trace, sensitivity, created_at
                    ) VALUES (%s, %s, %s, NULL, NULL, NULL, %s, 'MANUAL', %s, NULL, 'CONFIRMED', %s, '{}', '[]', '[]', %s)
                    """,
                    [
                        user.tenant_id,
                        matter_id,
                        ddl_id,
                        payload.label,
                        due_d,
                        owner_name,
                        now,
                    ],
                )

            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user.user_id,
                action="DEADLINE_CREATE",
                object_ref=ddl_id,
                matter_id=matter_id,
                decision="ALLOW",
                detail={"label": payload.label, "due_on": payload.due_on},
            )

        return {
            "deadline_id": ddl_id,
            "matter_id": matter_id,
            "rule_id": None,
            "label": payload.label,
            "kind": "MANUAL",
            "due_on": due_d.isoformat(),
            "lifecycle": "CONFIRMED",
            "owner": owner_name,
            "source_note": f"entered by {owner_name}, not computed",
            "created_at": now.isoformat(),
        }


@router.post("/deadlines/{deadline_id}/lifecycle", response=DeadlineResponse, auth=authz_required)
def update_deadline_lifecycle(
    request: HttpRequest, deadline_id: str, payload: DeadlineLifecycleRequest
) -> dict[str, Any]:
    """Update deadline lifecycle state (PROPOSED, CONFIRMED, DONE, WAIVED, MISSED)."""
    allowed = {"PROPOSED", "CONFIRMED", "DONE", "WAIVED", "MISSED"}
    if payload.lifecycle not in allowed:
        raise HttpError(400, f"Invalid lifecycle state. Allowed: {allowed}")

    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        deadline = Deadline.objects.filter(
            tenant_id=user.tenant_id, deadline_id=deadline_id
        ).first()
        if not deadline:
            raise HttpError(404, "Deadline not found.")

        matter = Matter.objects.filter(
            tenant_id=user.tenant_id, matter_id=deadline.matter_id
        ).first()
        if not matter or not authz.can(user, "write", matter):
            raise HttpError(403, "Access to modify this matter is forbidden.")

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE tpl.deadline
                    SET lifecycle = %s
                    WHERE tenant_id = %s AND deadline_id = %s
                    """,
                    [payload.lifecycle, user.tenant_id, deadline_id],
                )

            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user.user_id,
                action="DEADLINE_LIFECYCLE",
                object_ref=deadline_id,
                matter_id=deadline.matter_id,
                decision="ALLOW",
                detail={"lifecycle": payload.lifecycle},
            )

        updated = Deadline.objects.get(tenant_id=user.tenant_id, deadline_id=deadline_id)
        return {
            "deadline_id": updated.deadline_id,
            "matter_id": updated.matter_id,
            "rule_id": updated.rule_id,
            "label": updated.label,
            "kind": updated.kind,
            "due_on": updated.due_on.isoformat(),
            "lifecycle": updated.lifecycle,
            "owner": updated.owner,
            "source_note": (
                f"computed from {updated.rule_id}"
                if updated.rule_id
                else f"entered by {updated.owner or 'lawyer'}, not computed"
            ),
            "created_at": updated.created_at.isoformat(),
        }


# ==============================================================================
# Candidates ("Check these")
# ==============================================================================


@router.get("/candidates", response=list[CaseCandidateResponse], auth=authz_required)
def list_candidates(
    request: HttpRequest, matter_id: str | None = None
) -> list[dict[str, Any]]:
    """List pending case candidates requiring lawyer confirmation ('Check these')."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        qs = CaseCandidate.objects.filter(
            tenant_id=user.tenant_id, status="PENDING"
        )
        if matter_id:
            qs = qs.filter(matter_id=matter_id)

        candidates = qs.order_by("-created_at")
        results: list[dict[str, Any]] = []
        for c in candidates:
            matter = Matter.objects.filter(
                tenant_id=user.tenant_id, matter_id=c.matter_id
            ).first()
            if matter and authz.can(user, "read", matter):
                results.append(
                    {
                        "candidate_id": c.candidate_id,
                        "matter_id": c.matter_id,
                        "kind": c.kind,
                        "source": c.source,
                        "source_ref": c.source_ref,
                        "case_number_raw": c.case_number_raw,
                        "list_date": c.list_date.isoformat() if c.list_date else None,
                        "bench": c.bench,
                        "normalized_case_no": c.normalized_case_no,
                        "details": c.details or {},
                        "status": c.status,
                        "created_at": c.created_at.isoformat(),
                        "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
                        "resolved_by": c.resolved_by,
                    }
                )
        return results


@router.post("/candidates/{candidate_id}/confirm", auth=authz_required)
def confirm_candidate(request: HttpRequest, candidate_id: str) -> dict[str, Any]:
    """Confirm a candidate match and promote to active hearing/order."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        candidate = CaseCandidate.objects.filter(
            tenant_id=user.tenant_id, candidate_id=candidate_id
        ).first()
        if not candidate or candidate.status != "PENDING":
            raise HttpError(404, "Pending candidate not found.")

        matter = Matter.objects.filter(
            tenant_id=user.tenant_id, matter_id=candidate.matter_id
        ).first()
        if not matter or not authz.can(user, "write", matter):
            raise HttpError(403, "Access to modify this matter is forbidden.")

        now = timezone.now()
        with transaction.atomic():
            with connection.cursor() as cursor:
                if candidate.kind == "HEARING":
                    hrg_id = mint_id("hrg")
                    cursor.execute(
                        """
                        INSERT INTO tpl.hearing (
                            tenant_id, matter_id, hearing_id, date, court_no, item_no,
                            bench, purpose, source, source_ref, status, outcome,
                            next_date, entered_by, observed_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'CAUSE_LIST', %s, 'LISTED', NULL, NULL, %s, %s)
                        ON CONFLICT (tenant_id, matter_id, date, bench, court_no) WHERE source = 'CAUSE_LIST'
                        DO UPDATE SET item_no = EXCLUDED.item_no, observed_at = EXCLUDED.observed_at
                        """,
                        [
                            user.tenant_id,
                            candidate.matter_id,
                            hrg_id,
                            candidate.list_date,
                            candidate.details.get("court_no"),
                            candidate.details.get("item_no"),
                            candidate.bench or matter.court_or_forum,
                            candidate.details.get("purpose") or "Hearing",
                            candidate.source_ref,
                            user.user_id,
                            now,
                        ],
                    )
                elif candidate.kind == "ORDER":
                    cursor.execute(
                        """
                        INSERT INTO tpl.matter_dependency (
                            tenant_id, matter_id, public_id, match_key, as_of_legal_date,
                            kind, weight, source_ref, added_at
                        ) VALUES (%s, %s, %s, %s, %s, 'OWN_CASE', 1.0, %s, %s)
                        ON CONFLICT (tenant_id, matter_id, public_id, kind) DO NOTHING
                        """,
                        [
                            user.tenant_id,
                            candidate.matter_id,
                            candidate.source_ref,
                            candidate.normalized_case_no or candidate.case_number_raw,
                            candidate.list_date,
                            candidate.source_ref,
                            now,
                        ],
                    )

                cursor.execute(
                    """
                    UPDATE tpl.case_candidate
                    SET status = 'CONFIRMED', resolved_at = %s, resolved_by = %s
                    WHERE tenant_id = %s AND candidate_id = %s
                    """,
                    [now, user.user_id, user.tenant_id, candidate_id],
                )

            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user.user_id,
                action="CANDIDATE_CONFIRM",
                object_ref=candidate_id,
                matter_id=candidate.matter_id,
                decision="ALLOW",
                detail={"kind": candidate.kind, "raw_number": candidate.case_number_raw},
            )

        return {"status": "ok", "candidate_id": candidate_id, "resolved": "CONFIRMED"}


@router.post("/candidates/{candidate_id}/dismiss", auth=authz_required)
def dismiss_candidate(request: HttpRequest, candidate_id: str) -> dict[str, Any]:
    """Dismiss a candidate. Remembered permanently so the item never re-alerts."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        candidate = CaseCandidate.objects.filter(
            tenant_id=user.tenant_id, candidate_id=candidate_id
        ).first()
        if not candidate or candidate.status != "PENDING":
            raise HttpError(404, "Pending candidate not found.")

        matter = Matter.objects.filter(
            tenant_id=user.tenant_id, matter_id=candidate.matter_id
        ).first()
        if not matter or not authz.can(user, "write", matter):
            raise HttpError(403, "Access to modify this matter is forbidden.")

        now = timezone.now()
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE tpl.case_candidate
                    SET status = 'DISMISSED', resolved_at = %s, resolved_by = %s
                    WHERE tenant_id = %s AND candidate_id = %s
                    """,
                    [now, user.user_id, user.tenant_id, candidate_id],
                )

            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user.user_id,
                action="CANDIDATE_DISMISS",
                object_ref=candidate_id,
                matter_id=candidate.matter_id,
                decision="ALLOW",
                detail={"kind": candidate.kind, "raw_number": candidate.case_number_raw},
            )

        return {"status": "ok", "candidate_id": candidate_id, "resolved": "DISMISSED"}


# ==============================================================================
# Court Orders & Timeline
# ==============================================================================


@router.get("/matters/{matter_id}/orders", response=list[CourtOrderResponse], auth=authz_required)
def list_matter_orders(request: HttpRequest, matter_id: str) -> list[dict[str, Any]]:
    """List public court orders matched to this matter."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "read", matter):
            raise HttpError(403, "Access to this matter is forbidden.")

        deps = MatterDependency.objects.filter(
            tenant_id=user.tenant_id, matter_id=matter_id, kind="OWN_CASE"
        ).order_by("-added_at")

        return [
            {
                "matter_id": d.matter_id,
                "public_id": d.public_id,
                "match_key": d.match_key,
                "decision_date": d.as_of_legal_date.isoformat() if d.as_of_legal_date else None,
                "bench": matter.court_or_forum,
                "kind": d.kind,
                "source_ref": d.source_ref,
                "uncertified_badge": True,
                "source_viewer_url": f"/viewer/public/{d.public_id}",
            }
            for d in deps
        ]


@router.get("/matters/{matter_id}/timeline", response=list[TimelineItemResponse], auth=authz_required)
def get_matter_timeline(request: HttpRequest, matter_id: str) -> list[dict[str, Any]]:
    """Unified chronological timeline of hearings, dates, documents and orders."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "read", matter):
            raise HttpError(403, "Access to this matter is forbidden.")

        items: list[dict[str, Any]] = []

        # 1. Hearings
        hearings = Hearing.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id)
        for h in hearings:
            items.append(
                {
                    "id": h.hearing_id,
                    "date": h.date.isoformat(),
                    "item_type": "HEARING",
                    "title": f"Hearing: {h.bench or matter.court_or_forum or 'Court'} (Court {h.court_no or '-'}, Item {h.item_no or '-'})",
                    "subtitle": h.purpose or "Hearing listed",
                    "status": h.status,
                    "metadata": {
                        "hearing_id": h.hearing_id,
                        "source": h.source,
                        "outcome": h.outcome,
                        "court_no": h.court_no,
                        "item_no": h.item_no,
                    },
                }
            )

        # 2. Deadlines
        deadlines = Deadline.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id)
        for d in deadlines:
            items.append(
                {
                    "id": d.deadline_id,
                    "date": d.due_on.isoformat(),
                    "item_type": "DEADLINE",
                    "title": f"Deadline: {d.label}",
                    "subtitle": (
                        f"computed from {d.rule_id}"
                        if d.rule_id
                        else f"entered by {d.owner or 'lawyer'}, not computed"
                    ),
                    "status": d.lifecycle,
                    "metadata": {
                        "deadline_id": d.deadline_id,
                        "kind": d.kind,
                        "owner": d.owner,
                    },
                }
            )

        # 3. Documents
        docs = Pdoc.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id)
        for p in docs:
            items.append(
                {
                    "id": p.pdoc_id,
                    "date": p.created_at.date().isoformat(),
                    "item_type": "DOCUMENT",
                    "title": f"Document: {p.title or p.pdoc_id}",
                    "subtitle": f"Stage: {p.stage} | Provenance: {p.provenance}",
                    "status": p.stage,
                    "metadata": {
                        "pdoc_id": p.pdoc_id,
                        "doc_type": p.doc_type,
                        "current_version": p.current_version,
                    },
                }
            )

        # 4. Court Orders
        deps = MatterDependency.objects.filter(
            tenant_id=user.tenant_id, matter_id=matter_id, kind="OWN_CASE"
        )
        for dep in deps:
            order_date = (
                dep.as_of_legal_date.isoformat()
                if dep.as_of_legal_date
                else dep.added_at.date().isoformat()
            )
            items.append(
                {
                    "id": dep.public_id,
                    "date": order_date,
                    "item_type": "ORDER",
                    "title": f"Court Order: {dep.public_id}",
                    "subtitle": "Uncertified copy from official public mirror",
                    "status": "ORDER",
                    "metadata": {
                        "public_id": dep.public_id,
                        "match_key": dep.match_key,
                        "source_ref": dep.source_ref,
                    },
                }
            )

        # Sort descending by date
        items.sort(key=lambda x: str(x["date"]), reverse=True)
        return items


# ==============================================================================
# Today Dashboard & Calendar
# ==============================================================================


@router.get("/today", response=TodayResponse, auth=authz_required)
def get_today_dashboard(request: HttpRequest) -> dict[str, Any]:
    """Mobile-first Today dashboard answering: What is listed today/tomorrow, what is due, what came in."""
    user = _get_app_user(request)
    now_ist = timezone.now().astimezone(IST)
    today_d = now_ist.date()
    tomorrow_d = today_d + timedelta(days=1)
    week_end_d = today_d + timedelta(days=7)

    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        all_matters = Matter.objects.filter(tenant_id=user.tenant_id, status="ACTIVE")
        matters_map = {m.matter_id: m for m in all_matters if authz.can(user, "read", m)}
        matter_ids = list(matters_map.keys())

        if not matter_ids:
            return {
                "today_date": today_d.isoformat(),
                "today_hearings": [],
                "tomorrow_hearings": [],
                "this_week_hearings": [],
                "this_week_deadlines": [],
                "pending_candidates": [],
                "recent_orders": [],
                "total_active_matters": 0,
            }

        # Hearings
        all_hearings = (
            Hearing.objects.filter(
                tenant_id=user.tenant_id,
                matter_id__in=matter_ids,
                date__gte=today_d,
                date__lte=week_end_d,
            )
            .exclude(status="CANCELLED")
            .order_by("date", "court_no", "item_no")
        )

        today_hearings_list: list[dict[str, Any]] = []
        tomorrow_hearings_list: list[dict[str, Any]] = []
        this_week_hearings_list: list[dict[str, Any]] = []

        for h in all_hearings:
            m = matters_map.get(h.matter_id)
            m_title = m.title if m else "Matter"
            c_id = m.client_id if m else None
            court_forum = (
                h.bench
                if (h.source == "CAUSE_LIST" and h.bench)
                else ((m.court_or_forum if m else None) or h.bench)
            )

            item = {
                "hearing_id": h.hearing_id,
                "matter_id": h.matter_id,
                "matter_title": m_title,
                "client_id": c_id,
                "court_or_forum": court_forum,
                "court_no": h.court_no,
                "item_no": h.item_no,
                "bench": h.bench,
                "purpose": h.purpose,
                "status": h.status,
                "date": h.date.isoformat(),
            }

            if h.date == today_d:
                today_hearings_list.append(item)
            elif h.date == tomorrow_d:
                tomorrow_hearings_list.append(item)
            this_week_hearings_list.append(item)

        # Deadlines
        active_deadlines = Deadline.objects.filter(
            tenant_id=user.tenant_id,
            matter_id__in=matter_ids,
            due_on__lte=week_end_d,
            lifecycle__in=["PROPOSED", "CONFIRMED"],
        ).order_by("due_on")

        this_week_deadlines_list: list[dict[str, Any]] = []
        for d in active_deadlines:
            m = matters_map.get(d.matter_id)
            m_title = m.title if m else "Matter"
            is_overdue = d.due_on < today_d
            source_note = (
                f"computed from {d.rule_id}"
                if d.rule_id
                else f"entered by {d.owner or 'lawyer'}, not computed"
            )
            this_week_deadlines_list.append(
                {
                    "deadline_id": d.deadline_id,
                    "matter_id": d.matter_id,
                    "matter_title": m_title,
                    "label": d.label,
                    "due_on": d.due_on.isoformat(),
                    "lifecycle": d.lifecycle,
                    "source_note": source_note,
                    "is_overdue": is_overdue,
                }
            )

        # Pending Candidates ("Check these")
        candidates = CaseCandidate.objects.filter(
            tenant_id=user.tenant_id,
            matter_id__in=matter_ids,
            status="PENDING",
        ).order_by("-created_at")

        pending_candidates_list = [
            {
                "candidate_id": c.candidate_id,
                "matter_id": c.matter_id,
                "kind": c.kind,
                "source": c.source,
                "source_ref": c.source_ref,
                "case_number_raw": c.case_number_raw,
                "list_date": c.list_date.isoformat() if c.list_date else None,
                "bench": c.bench,
                "normalized_case_no": c.normalized_case_no,
                "details": c.details or {},
                "status": c.status,
                "created_at": c.created_at.isoformat(),
                "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
                "resolved_by": c.resolved_by,
            }
            for c in candidates
        ]

        # Recent Orders
        recent_deps = MatterDependency.objects.filter(
            tenant_id=user.tenant_id,
            matter_id__in=matter_ids,
            kind="OWN_CASE",
        ).order_by("-added_at")[:10]

        recent_orders_list = [
            {
                "matter_id": dep.matter_id,
                "public_id": dep.public_id,
                "match_key": dep.match_key,
                "decision_date": dep.as_of_legal_date.isoformat() if dep.as_of_legal_date else None,
                "bench": None,
                "kind": dep.kind,
                "source_ref": dep.source_ref,
                "uncertified_badge": True,
                "source_viewer_url": f"/viewer/public/{dep.public_id}",
            }
            for dep in recent_deps
        ]

        return {
            "today_date": today_d.isoformat(),
            "today_hearings": today_hearings_list,
            "tomorrow_hearings": tomorrow_hearings_list,
            "this_week_hearings": this_week_hearings_list,
            "this_week_deadlines": this_week_deadlines_list,
            "pending_candidates": pending_candidates_list,
            "recent_orders": recent_orders_list,
            "total_active_matters": len(matters_map),
        }


def _generate_ical_calendar(
    events: list[dict[str, Any]], cal_name: str = "Lawyer Brain Calendar"
) -> str:
    """Generate RFC 5545 compliant iCalendar string with all-day VALUE=DATE events."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Lawyer Brain//Legal Intelligence Platform//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{cal_name}",
        "X-WR-TIMEZONE:Asia/Kolkata",
    ]
    now_stamp = timezone.now().strftime("%Y%m%dT%H%M%SZ")
    for ev in events:
        start_d: date = ev["date"]
        end_d: date = start_d + timedelta(days=1)
        start_str = start_d.strftime("%Y%m%d")
        end_str = end_d.strftime("%Y%m%d")
        uid = ev["uid"]
        summary = (
            str(ev["summary"])
            .replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", " ")
        )
        desc = (
            str(ev.get("description", ""))
            .replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n")
        )
        loc = (
            str(ev.get("location", ""))
            .replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", " ")
        )
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}@lawyerbrain")
        lines.append(f"DTSTAMP:{now_stamp}")
        lines.append(f"DTSTART;VALUE=DATE:{start_str}")
        lines.append(f"DTEND;VALUE=DATE:{end_str}")
        lines.append(f"SUMMARY:{summary}")
        if desc:
            lines.append(f"DESCRIPTION:{desc}")
        if loc:
            lines.append(f"LOCATION:{loc}")
        lines.append("STATUS:CONFIRMED")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


@router.get("/matters/{matter_id}/calendar/export", auth=authz_required)
def export_matter_calendar(request: HttpRequest, matter_id: str) -> HttpResponse:
    """Export matter hearings and deadlines as RFC 5545 all-day iCalendar file."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        matter = Matter.objects.filter(tenant_id=user.tenant_id, matter_id=matter_id).first()
        if not matter or not authz.can(user, "read", matter):
            raise HttpError(403, "Access to this matter is forbidden.")

        events: list[dict[str, Any]] = []

        hearings = Hearing.objects.filter(
            tenant_id=user.tenant_id, matter_id=matter_id
        ).exclude(status="CANCELLED")
        for h in hearings:
            events.append(
                {
                    "uid": f"hearing-{h.hearing_id}",
                    "date": h.date,
                    "summary": f"Hearing: {matter.title} ({h.bench or matter.court_or_forum or 'Court'})",
                    "location": f"Court {h.court_no or '-'}, Item {h.item_no or '-'}",
                    "description": f"Purpose: {h.purpose or 'Hearing'}\\nStatus: {h.status}\\nSource: {h.source}",
                }
            )

        deadlines = Deadline.objects.filter(
            tenant_id=user.tenant_id,
            matter_id=matter_id,
            lifecycle__in=["PROPOSED", "CONFIRMED"],
        )
        for d in deadlines:
            events.append(
                {
                    "uid": f"deadline-{d.deadline_id}",
                    "date": d.due_on,
                    "summary": f"Due: {d.label} - {matter.title}",
                    "location": matter.court_or_forum or "",
                    "description": f"entered by {d.owner or 'lawyer'}, not computed\\nLifecycle: {d.lifecycle}",
                }
            )

        record_audit_event(
            tenant_id=user.tenant_id,
            actor=user.user_id,
            action="CALENDAR_EXPORT",
            object_ref=matter_id,
            matter_id=matter_id,
            decision="ALLOW",
            detail={"events_count": len(events)},
        )

        ics_content = _generate_ical_calendar(events, cal_name=f"Matter {matter.title}")
        response = HttpResponse(ics_content, content_type="text/calendar; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="matter_{matter_id}_calendar.ics"'
        return response


@router.get("/calendar/export", auth=authz_required)
def export_firm_calendar(request: HttpRequest) -> HttpResponse:
    """Export all accessible hearings and deadlines as RFC 5545 all-day iCalendar file."""
    user = _get_app_user(request)
    with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
        all_matters = Matter.objects.filter(tenant_id=user.tenant_id, status="ACTIVE")
        matters_map = {m.matter_id: m for m in all_matters if authz.can(user, "read", m)}
        matter_ids = list(matters_map.keys())

        events: list[dict[str, Any]] = []

        hearings = Hearing.objects.filter(
            tenant_id=user.tenant_id, matter_id__in=matter_ids
        ).exclude(status="CANCELLED")
        for h in hearings:
            m = matters_map.get(h.matter_id)
            m_title = m.title if m else "Matter"
            events.append(
                {
                    "uid": f"hearing-{h.hearing_id}",
                    "date": h.date,
                    "summary": f"Hearing: {m_title} ({h.bench or (m.court_or_forum if m else None) or 'Court'})",
                    "location": f"Court {h.court_no or '-'}, Item {h.item_no or '-'}",
                    "description": f"Purpose: {h.purpose or 'Hearing'}\\nStatus: {h.status}\\nSource: {h.source}",
                }
            )

        deadlines = Deadline.objects.filter(
            tenant_id=user.tenant_id,
            matter_id__in=matter_ids,
            lifecycle__in=["PROPOSED", "CONFIRMED"],
        )
        for d in deadlines:
            m = matters_map.get(d.matter_id)
            m_title = m.title if m else "Matter"
            events.append(
                {
                    "uid": f"deadline-{d.deadline_id}",
                    "date": d.due_on,
                    "summary": f"Due: {d.label} - {m_title}",
                    "location": (m.court_or_forum if m else "") or "",
                    "description": f"entered by {d.owner or 'lawyer'}, not computed\\nLifecycle: {d.lifecycle}",
                }
            )

        record_audit_event(
            tenant_id=user.tenant_id,
            actor=user.user_id,
            action="CALENDAR_EXPORT",
            object_ref="firm",
            decision="ALLOW",
            detail={"events_count": len(events)},
        )

        ics_content = _generate_ical_calendar(events, cal_name="Lawyer Brain - Court Calendar")
        response = HttpResponse(ics_content, content_type="text/calendar; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="lawyer_brain_calendar.ics"'
        return response

