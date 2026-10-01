"""Append-only cryptographic hash-chained audit logging for tenant workspace.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.8: tpl.audit_event
- docs/09_P7_firm_matter_workspace.md line 723: SHA-256(prev_hash || canonical_json)
- Session S03 Directive #6: Transactional advisory locking per tenant to prevent hash chain forks
- Session S03 follow-up: O(1) audit chain head table and verify_chain(tenant)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

from django.db import connections, router, transaction
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
    using: str | None = None,
) -> AuditEvent:
    """Record an append-only audit event with strict SHA-256 hash chaining.

    Serializes writes per tenant via PostgreSQL advisory transaction locks
    (pg_advisory_xact_lock) and reads the chain head in O(1) from tpl.audit_chain_head.
    """
    if using is None:
        using = router.db_for_write(AuditEvent) or "default"

    with transaction.atomic(using=using):
        with connections[using].cursor() as cursor:
            # Enforce tenant isolation under RLS for this transaction
            cursor.execute("SET LOCAL app.tenant_id = %s;", [tenant_id])

            # 1. Acquire transaction-scoped advisory lock for this tenant's audit chain
            lock_key = f"audit_{tenant_id}"
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [lock_key])

            # 2. Get current chain head for this tenant from tpl.audit_chain_head (O(1))
            cursor.execute(
                """
                SELECT latest_hash, seq, updated_at
                FROM tpl.audit_chain_head
                WHERE tenant_id = %s
                FOR UPDATE;
                """,
                [tenant_id],
            )
            head = cursor.fetchone()
            if head:
                prev_hash = bytes(head[0])
                seq = int(head[1]) + 1
                latest_at = head[2]
                if at is None:
                    now = timezone.now()
                    at = max(now, latest_at + timedelta(microseconds=1))
            else:
                # Genesis block hash (32 zero bytes)
                prev_hash = b"\x00" * 32
                seq = 1
                if at is None:
                    at = timezone.now()

            if detail is None:
                detail = {}

            audit_id = mint_id("adt")

            # 3. Canonical JSON of row payload (including monotonic sequence)
            row_payload = {
                "action": action,
                "actor": actor,
                "at": at.isoformat(),
                "audit_id": audit_id,
                "decision": decision,
                "detail": detail,
                "matter_id": matter_id,
                "object_ref": object_ref,
                "seq": seq,
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
                    prev_hash, row_hash, seq
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    seq,
                ],
            )

            # 6. Update tpl.audit_chain_head (O(1))
            cursor.execute(
                """
                INSERT INTO tpl.audit_chain_head (
                    tenant_id, latest_audit_id, latest_hash, seq, updated_at
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id) DO UPDATE SET
                    latest_audit_id = EXCLUDED.latest_audit_id,
                    latest_hash = EXCLUDED.latest_hash,
                    seq = EXCLUDED.seq,
                    updated_at = EXCLUDED.updated_at;
                """,
                [tenant_id, audit_id, row_hash, seq, at],
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
        seq=seq,
    )


def verify_chain(tenant_id: str, using: str | None = None) -> tuple[bool, str | None]:
    """Cryptographically verify the entire audit event hash chain for a tenant.

    Walks all events for the tenant in ascending sequence order and asserts:
    1. Sequence numbers start at 1 and advance monotonically without gaps.
    2. Genesis event has prev_hash = 32 zero bytes.
    3. Every subsequent event has prev_hash matching the prior event's row_hash.
    4. Every event has row_hash = SHA-256(prev_hash || canonical_json).
    5. Timestamps are monotonically non-decreasing.

    Returns:
        (True, None) if the chain is fully verified and uncorrupted.
        (False, error_reason) if any tampering or broken link is detected.
    """
    if using is None:
        using = router.db_for_read(AuditEvent) or "default"

    with transaction.atomic(using=using):
        with connections[using].cursor() as cursor:
            cursor.execute("SET LOCAL app.tenant_id = %s;", [tenant_id])
            cursor.execute(
                """
                SELECT audit_id, at, actor, action, object_ref, matter_id,
                       decision, detail, prev_hash, row_hash, seq
                FROM tpl.audit_event
                WHERE tenant_id = %s
                ORDER BY seq ASC;
                """,
                [tenant_id],
            )
            rows = cursor.fetchall()

    if not rows:
        return True, None

    expected_prev_hash = b"\x00" * 32
    expected_seq = 1
    prev_at: datetime | None = None

    for row in rows:
        (
            audit_id,
            at,
            actor,
            action,
            object_ref,
            matter_id,
            decision,
            detail,
            prev_hash,
            row_hash,
            seq,
        ) = row

        prev_hash_bytes = bytes(prev_hash) if prev_hash else b""
        row_hash_bytes = bytes(row_hash)

        # 1. Sequence continuity
        if seq != expected_seq:
            return (
                False,
                f"Sequence gap at {audit_id}: expected {expected_seq}, got {seq}",
            )

        # 2. Hash link continuity
        if prev_hash_bytes != expected_prev_hash:
            return (
                False,
                f"Broken hash chain at {audit_id} (seq {seq}): prev_hash does not match prior row_hash",
            )

        # 3. Monotonic timestamps
        if prev_at and at < prev_at:
            return (
                False,
                f"Non-monotonic timestamp at {audit_id} (seq {seq}): {at} < {prev_at}",
            )

        # 4. Recompute canonical payload and SHA-256 hash
        row_payload = {
            "action": action,
            "actor": actor,
            "at": at.isoformat(),
            "audit_id": audit_id,
            "decision": decision,
            "detail": detail if detail is not None else {},
            "matter_id": matter_id,
            "object_ref": object_ref,
            "seq": seq,
            "tenant_id": tenant_id,
        }
        canonical_bytes = json.dumps(row_payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        hasher = hashlib.sha256()
        hasher.update(expected_prev_hash)
        hasher.update(canonical_bytes)
        computed_hash = hasher.digest()

        if computed_hash != row_hash_bytes:
            return (
                False,
                f"Hash mismatch at {audit_id} (seq {seq}): payload altered",
            )

        expected_prev_hash = row_hash_bytes
        expected_seq += 1
        prev_at = at

    return True, None
