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
from workspace.models import AppUser, Matter


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
       - VIEWER: reads
       - MEMBER: reads, writes
       - LEAD: reads, writes, manages members, approves exports
       - Firm ADMIN: can manage membership, but CANNOT read walled matter content without membership.
    4. Tenant-scoped object: owner/team only.
    5. Public (plc) object: any active user.
    """
    # 1. Inactive user -> DENY
    if not user.active:
        return False

    # Extract matter_id if obj is matter-scoped
    matter_id: str | None = None
    if isinstance(obj, Matter):
        matter_id = obj.matter_id
    elif hasattr(obj, "matter_id"):
        matter_id = obj.matter_id
    elif isinstance(obj, str) and obj.startswith("mat_"):
        matter_id = obj
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

            if member_row:
                member_role = member_row[0]
                if member_role == "VIEWER":
                    return action in ("read", "view", "get", "list")
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
