"""Workspace shared domain write services.

Normative sources:
- Session R3 Correction 10: Reuse existing write paths for clients, matters,
  case links, and hearings across both REST routes and bulk Excel/CSV imports,
  guaranteeing unified normalization, LEAD memberships, and audit trails.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from django.db import connection, transaction
from django.utils import timezone

from anchor_lib.case_numbers import normalize_case_number
from anchor_lib.ids import mint_id
from workspace.audit import record_audit_event


def create_client_service(
    tenant_id: str,
    actor_id: str,
    display_name: str,
    client_type: str = "COMPANY",
    identifiers: dict[str, Any] | None = None,
    contact: dict[str, Any] | None = None,
    notes: str | None = None,
    import_id: str | None = None,
) -> dict[str, Any]:
    """Create a client entity with audit logging and return the created record."""
    client_id = mint_id("cli")
    now = timezone.now()
    clean_identifiers = identifiers or {}
    clean_contact = contact or {}

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
                    tenant_id,
                    client_id,
                    display_name,
                    client_type,
                    json.dumps(clean_identifiers),
                    json.dumps(clean_contact),
                    notes,
                    actor_id,
                    now,
                ],
            )

        detail: dict[str, Any] = {
            "display_name": display_name,
            "client_type": client_type,
        }
        if import_id:
            detail["import_id"] = import_id

        record_audit_event(
            tenant_id=tenant_id,
            actor=actor_id,
            action="CLIENT_CREATE",
            object_ref=client_id,
            decision="ALLOW",
            detail=detail,
        )

    return {
        "client_id": client_id,
        "display_name": display_name,
        "client_type": client_type,
        "identifiers": clean_identifiers,
        "contact": clean_contact,
        "notes": notes,
        "status": "ACTIVE",
        "created_by": actor_id,
        "created_at": now.isoformat(),
    }


def create_matter_service(
    tenant_id: str,
    actor_id: str,
    client_id: str,
    title: str,
    client_role: str = "PETITIONER",
    case_type: str | None = None,
    court_or_forum: str | None = None,
    jurisdiction_state: str | None = None,
    client_matter_no: str | None = None,
    walled: bool = False,
    additional_lead_user_id: str | None = None,
    import_id: str | None = None,
) -> dict[str, Any]:
    """Open a matter under a client, establish LEAD memberships, and record audit event."""
    from workspace.models import CLIENT_ROLES

    if client_role not in CLIENT_ROLES:
        raise ValueError(f"Invalid client_role '{client_role}'. Must be one of: {', '.join(CLIENT_ROLES)}")

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
                    tenant_id,
                    matter_id,
                    client_id,
                    client_matter_no,
                    title,
                    client_role,
                    case_type,
                    court_or_forum,
                    jurisdiction_state,
                    walled,
                    now,
                ],
            )

            # Actor is always added as LEAD member
            cursor.execute(
                """
                INSERT INTO tpl.matter_member (
                    tenant_id, matter_id, user_id, role, granted_by, granted_at
                ) VALUES (%s, %s, %s, 'LEAD', %s, %s)
                ON CONFLICT (tenant_id, matter_id, user_id, granted_at) DO NOTHING
                """,
                [tenant_id, matter_id, actor_id, actor_id, now],
            )

            # Additional lead lawyer (e.g. from import lead lawyer email)
            if additional_lead_user_id and additional_lead_user_id != actor_id:
                cursor.execute(
                    """
                    INSERT INTO tpl.matter_member (
                        tenant_id, matter_id, user_id, role, granted_by, granted_at
                    ) VALUES (%s, %s, %s, 'LEAD', %s, %s)
                    ON CONFLICT (tenant_id, matter_id, user_id, granted_at) DO NOTHING
                    """,
                    [tenant_id, matter_id, additional_lead_user_id, actor_id, now],
                )

        detail: dict[str, Any] = {
            "client_id": client_id,
            "title": title,
            "case_type": case_type,
            "court": court_or_forum,
        }
        if additional_lead_user_id:
            detail["additional_lead_user_id"] = additional_lead_user_id
        if import_id:
            detail["import_id"] = import_id

        record_audit_event(
            tenant_id=tenant_id,
            actor=actor_id,
            action="MATTER_CREATE",
            object_ref=matter_id,
            matter_id=matter_id,
            decision="ALLOW",
            detail=detail,
        )

    return {
        "matter_id": matter_id,
        "client_id": client_id,
        "title": title,
        "client_role": client_role,
        "case_type": case_type,
        "court_or_forum": court_or_forum,
        "status": "ACTIVE",
        "created_at": now.isoformat(),
    }


def create_case_link_service(
    tenant_id: str,
    actor_id: str,
    matter_id: str,
    value_raw: str,
    scheme: str = "IN_COURT",
    role: str = "MAIN",
    track: bool = True,
    import_id: str | None = None,
) -> dict[str, Any]:
    """Link a case number to a matter, normalize on write, and record audit event."""
    parsed = normalize_case_number(value_raw)
    if parsed.parseable:
        val = parsed.canonical
        parseable = True
        actual_track = track
        warning = None
    else:
        val = value_raw.strip()
        parseable = False
        # Correction 10: Save unreadable case numbers with track = false
        actual_track = False
        warning = (
            f"Case number '{value_raw}' could not be canonically parsed; "
            "it will not be tracked automatically."
        )

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
                    tenant_id,
                    matter_id,
                    scheme,
                    val,
                    role,
                    actual_track,
                ],
            )

        detail: dict[str, Any] = {
            "scheme": scheme,
            "raw": value_raw,
            "normalized": val,
            "parseable": parseable,
        }
        if import_id:
            detail["import_id"] = import_id

        record_audit_event(
            tenant_id=tenant_id,
            actor=actor_id,
            action="CASE_LINK_ADD",
            object_ref=f"{scheme}:{val}",
            matter_id=matter_id,
            decision="ALLOW",
            detail=detail,
        )

    return {
        "matter_id": matter_id,
        "scheme": scheme,
        "value_normalized": val,
        "role": role,
        "track": actual_track,
        "parseable": parseable,
        "warning": warning,
    }


def create_hearing_service(
    tenant_id: str,
    actor_id: str,
    matter_id: str,
    hearing_date: date,
    court_no: str | None = None,
    item_no: str | None = None,
    bench: str | None = None,
    purpose: str | None = None,
    source: str = "MANUAL",
    source_ref: str | None = None,
    status: str = "LISTED",
    outcome: str | None = None,
    notes: str | None = None,
    import_id: str | None = None,
) -> dict[str, Any]:
    """Record a court hearing and write audit event."""
    hrg_id = mint_id("hrg")
    now = timezone.now()

    actual_outcome = outcome

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tpl.hearing (
                    tenant_id, matter_id, hearing_id, date, court_no, item_no,
                    bench, purpose, source, source_ref, status, outcome,
                    next_date, entered_by, observed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, %s, %s)
                """,
                [
                    tenant_id,
                    matter_id,
                    hrg_id,
                    hearing_date,
                    court_no,
                    item_no,
                    bench,
                    purpose,
                    source,
                    source_ref,
                    status,
                    actual_outcome,
                    actor_id,
                    now,
                ],
            )

        detail: dict[str, Any] = {
            "matter_id": matter_id,
            "date": hearing_date.isoformat(),
            "source": source,
        }
        if notes:
            detail["notes"] = notes
        if import_id:
            detail["import_id"] = import_id

        record_audit_event(
            tenant_id=tenant_id,
            actor=actor_id,
            action="HEARING_CREATE",
            object_ref=hrg_id,
            matter_id=matter_id,
            decision="ALLOW",
            detail=detail,
        )

    return {
        "hearing_id": hrg_id,
        "matter_id": matter_id,
        "date": hearing_date.isoformat(),
        "court_no": court_no,
        "item_no": item_no,
        "bench": bench,
        "purpose": purpose,
        "source": source,
        "source_ref": source_ref,
        "status": status,
        "outcome": actual_outcome,
        "entered_by": actor_id,
        "observed_at": now.isoformat(),
    }
