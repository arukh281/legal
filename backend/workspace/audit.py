"""Append-only cryptographic hash-chained audit logging for tenant workspace.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.8: tpl.audit_event
- docs/09_P7_firm_matter_workspace.md line 723: SHA-256(prev_hash || canonical_json)
- Session S03 Directive #6: Transactional advisory locking per tenant to prevent hash chain forks
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

from django.db import connection, transaction
from django.utils import timezone

from anchor_lib.ids import mint_id
from workspace.models import AuditEvent


def record_audit_event(
    tenant_id: str,
    actor: str,
    action: str,
    object_ref: str | None = None,
    matter_id: str | None = None,
    decision: str | None = None,
    detail: dict[str, Any] | None = None,
    at: datetime | None = None,
) -> AuditEvent:
    """Record an append-only audit event with strict SHA-256 hash chaining.

    Serializes writes per tenant via PostgreSQL advisory transaction locks
    (pg_advisory_xact_lock) so concurrent inserts cannot fork the chain.
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            # 1. Acquire transaction-scoped advisory lock for this tenant's audit chain
            lock_key = f"audit_{tenant_id}"
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [lock_key])

            # 2. Get current chain head for this tenant (the row not referenced as prev_hash by any row)
            cursor.execute(
                """
                SELECT row_hash, at
                FROM tpl.audit_event
                WHERE tenant_id = %s
                  AND row_hash NOT IN (
                      SELECT prev_hash
                      FROM tpl.audit_event
                      WHERE tenant_id = %s AND prev_hash IS NOT NULL
                  )
                LIMIT 1
                """,
                [tenant_id, tenant_id],
            )
            latest = cursor.fetchone()
            if latest and latest[0]:
                prev_hash = bytes(latest[0])
                latest_at = latest[1]
                if at is None:
                    now = timezone.now()
                    at = max(now, latest_at + timedelta(microseconds=1))
            else:
                # Genesis block hash (32 zero bytes)
                prev_hash = b"\x00" * 32
                if at is None:
                    at = timezone.now()

            if detail is None:
                detail = {}

            audit_id = mint_id("adt")

            # 3. Canonical JSON of row payload (excluding prev_hash and row_hash)
            row_payload = {
                "action": action,
                "actor": actor,
                "at": at.isoformat(),
                "audit_id": audit_id,
                "decision": decision,
                "detail": detail,
                "matter_id": matter_id,
                "object_ref": object_ref,
                "tenant_id": tenant_id,
            }
            canonical_bytes = json.dumps(row_payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )

            # 4. Compute row_hash = SHA-256(prev_hash || canonical_bytes)
            hasher = hashlib.sha256()
            hasher.update(prev_hash)
            hasher.update(canonical_bytes)
            row_hash = hasher.digest()

            # 5. Insert directly into tpl.audit_event
            cursor.execute(
                """
                INSERT INTO tpl.audit_event (
                    tenant_id, audit_id, at, actor, action,
                    object_ref, matter_id, decision, detail,
                    prev_hash, row_hash
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    tenant_id,
                    audit_id,
                    at,
                    actor,
                    action,
                    object_ref,
                    matter_id,
                    decision,
                    json.dumps(detail),
                    prev_hash,
                    row_hash,
                ],
            )

    return AuditEvent(
        tenant_id=tenant_id,
        audit_id=audit_id,
        at=at,
        actor=actor,
        action=action,
        object_ref=object_ref,
        matter_id=matter_id,
        decision=decision,
        detail=detail,
        prev_hash=prev_hash,
        row_hash=row_hash,
    )
