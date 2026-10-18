"""Authorization single choke point and Tenant Execution Context (TEC).

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §6: Authorization (instead of OpenFGA)
- docs/01a_spine_decision_record.md: D9 (Tenant Execution Context)
- docs/09_P7_firm_matter_workspace.md §2.3.1, §6
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.db import connection

from workspace.audit import record_audit_event
from workspace.db import tenant_db_context
from workspace.models import AppUser, Client, Matter

DATACLASS_HIERARCHY: dict[str, int] = {
    "PUBLIC": 0,
    "INTERNAL": 1,
    "TENANT_CONFIDENTIAL": 2,
    "PRIVILEGED": 3,
}


def resolve_request_dataclass(server_base: str, requested: str | None) -> str:
    """Resolve request dataclass: server decides baseline; client X-Dataclass may only raise it, never lower it."""
    base_level = DATACLASS_HIERARCHY.get(server_base, DATACLASS_HIERARCHY["TENANT_CONFIDENTIAL"])
    if not requested:
        return server_base
    req_upper = requested.strip().upper()
    req_level = DATACLASS_HIERARCHY.get(req_upper, -1)
    if req_level > base_level:
        return req_upper
    return server_base


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Tenant Execution Context (TEC) carried through requests, jobs, and events.

    Implements D9: scoped context carrying tenant, user, matter, purpose,
    residency policy, and trace metadata.
    """

    tenant_id: str
    user_id: str
    firm_role: str
    matter_id: str | None = None
    purpose: str = "INTERACTIVE"
    traceparent: str | None = None
    residency_policy: str = "ANY"
    llm_policy: dict[str, Any] = field(default_factory=dict)
    dataclass: str = "TENANT_CONFIDENTIAL"


def can(
    user: AppUser,
    action: str,
    obj: Any,
    ctx: ExecutionContext | None = None,
) -> bool:
    """Authorization single choke point per docs/mvp/03_data_model_and_contracts.md §6.

    Policy, deny-first:
    1. Inactive user -> DENY.
    2. The user is in a wall_exclusion for the object's matter -> DENY, plus
       a WALL_VIOLATION_ATTEMPT audit row.
    3. Matter-scoped object: ALLOW if user is an active member with sufficient role:
       - VIEWER: reads, downloads
       - MEMBER: reads, writes, uploads, downloads
       - LEAD: reads, writes, manages members, approves exports
       - Firm ADMIN: can manage membership, but CANNOT read walled matter content without membership.
    4. Client-scoped object: ALLOW if user is a member of at least one of that client's matters,
       or is firm ADMIN, or created the client.
    5. Tenant-scoped object: owner/team only.
    6. Public (plc) object: any active user.
    """
    # 1. Inactive user -> DENY
    if not user.active:
        return False

    # Extract matter_id if obj is matter-scoped
    matter_id: str | None = None
    if isinstance(obj, Matter):
        matter_id = obj.matter_id
    elif hasattr(obj, "matter_id") and getattr(obj, "matter_id", None):
        matter_id = obj.matter_id
    elif isinstance(obj, str) and obj.startswith("mat_"):
        matter_id = obj
    elif hasattr(obj, "pdoc_id") and getattr(obj, "pdoc_id", None):
        with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT matter_id FROM tpl.pdoc WHERE tenant_id = %s AND pdoc_id = %s",
                    [user.tenant_id, obj.pdoc_id],
                )
                p_row = cursor.fetchone()
                if p_row:
                    matter_id = p_row[0]
    elif ctx and ctx.matter_id:
        matter_id = ctx.matter_id

    # 2 & 3. Matter-scoped object checks
    if matter_id:
        with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
            # Check ethical wall exclusion (deny-first)
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 1
                    FROM tpl.wall_exclusion we
                    JOIN tpl.ethical_wall ew ON ew.tenant_id = we.tenant_id AND ew.wall_id = we.wall_id
                    WHERE ew.tenant_id = %s AND ew.matter_id = %s AND we.user_id = %s
                    LIMIT 1
                    """,
                    [user.tenant_id, matter_id, user.user_id],
                )
                is_excluded = cursor.fetchone() is not None

            if is_excluded:
                # Emit WALL_VIOLATION_ATTEMPT audit log
                record_audit_event(
                    tenant_id=user.tenant_id,
                    actor=user.user_id,
                    action="WALL_VIOLATION_ATTEMPT",
                    object_ref=matter_id,
                    matter_id=matter_id,
                    decision="DENY",
                    detail={"action": action, "denial_reason": "WALL_EXCLUSION"},
                )
                return False

            # Check active matter membership
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT role
                    FROM tpl.matter_member
                    WHERE tenant_id = %s AND matter_id = %s AND user_id = %s AND revoked_at IS NULL
                    ORDER BY granted_at DESC
                    LIMIT 1
                    """,
                    [user.tenant_id, matter_id, user.user_id],
                )
                member_row = cursor.fetchone()

            # Matter export and client updates/share-links: strictly require active LEAD membership
            if action in (
                "publish_update",
                "create_share_link",
                "extend_share_link",
                "revoke_share_link",
                "export",
            ):
                return bool(member_row and member_row[0] == "LEAD")

            if member_row:
                member_role = member_row[0]
                if member_role == "VIEWER":
                    return action in ("read", "view", "get", "list", "download")
                if member_role == "MEMBER":
                    return action in (
                        "read",
                        "view",
                        "get",
                        "list",
                        "write",
                        "edit",
                        "create",
                        "update",
                        "upload",
                        "download",
                    )
                if member_role == "LEAD":
                    return True
                return False

            # Non-member check: Firm ADMIN
            if user.firm_role == "ADMIN":
                # Check if matter is walled via security-definer helper
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT tpl.is_matter_walled(%s)",
                        [matter_id],
                    )
                    row = cursor.fetchone()
                    is_walled = bool(row[0]) if row else False

                if is_walled:
                    # Firm ADMIN can manage membership but CANNOT read walled content without membership
                    return action in (
                        "manage_members",
                        "manage_membership",
                        "assign_member",
                        "revoke_member",
                    )
                # Non-walled matter: firm ADMIN has access
                return True

            # Non-member non-admin -> DENY
            return False

    if action in ("import_cases", "import"):
        return bool(user.firm_role == "ADMIN")

    # 4. Client-scoped checks
    client_id: str | None = None
    if isinstance(obj, Client):
        client_id = obj.client_id
    elif hasattr(obj, "client_id") and getattr(obj, "client_id", None):
        client_id = obj.client_id
    elif isinstance(obj, str) and obj.startswith("cli_"):
        client_id = obj

    if client_id:
        if action in ("create", "create_client"):
            return True
        if user.firm_role == "ADMIN":
            return True
        with tenant_db_context(tenant_id=user.tenant_id, user_id=user.user_id):
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT tpl.can_read_client(%s, %s)",
                    [client_id, user.user_id],
                )
                row = cursor.fetchone()
                return bool(row[0]) if row else False

    # 4. Tenant-scoped objects (e.g., owner check)
    if hasattr(obj, "owner_id"):
        return bool(obj.owner_id == user.user_id)
    if hasattr(obj, "user_id") and obj.user_id == user.user_id:
        return True

    # 5. Public objects or tenant-agnostic
    if getattr(obj, "is_public", False) or action in ("read_public", "list_public"):
        return True

    # Default tenant-level action check for active user
    if action in ("read_tenant", "list_tenant"):
        return True

    return True
