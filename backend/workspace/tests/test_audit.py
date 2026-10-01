"""Tests for tpl.audit_event append-only enforcement, cryptographic hash chaining, and concurrency serialization.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.8: tpl.audit_event
- Session S03 Directive #6: Truly append-only (revoke/trigger), serialized hash chain per tenant (advisory lock), concurrency test.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json

import pytest
from django.db import connection, connections, transaction

from anchor_lib.ids import mint_id
from workspace.audit import record_audit_event, verify_chain
from workspace.db import tenant_db_context
from workspace.models import AuditEvent, Tenant

pytestmark = pytest.mark.django_db(databases="__all__", transaction=True)


@pytest.fixture
def audit_tenant() -> Tenant:
    t_id = mint_id("ten")
    with tenant_db_context(tenant_id=t_id):
        return Tenant.objects.create(
            tenant_id=t_id,
            name="Audit Test Firm",
            idp={"kind": "GOOGLE", "tenant_or_domain": "firm.in"},
        )


def test_audit_event_hash_chain_integrity(audit_tenant: Tenant) -> None:
    """Sequential audit events correctly link via SHA-256(prev_hash || canonical_json)."""
    t_id = audit_tenant.tenant_id
    actions = [
        "USER_LOGIN",
        "MATTER_CREATED",
        "DOCUMENT_UPLOADED",
        "EXPORT_APPROVED",
        "USER_LOGOUT",
    ]

    recorded: list[AuditEvent] = []
    for action in actions:
        ev = record_audit_event(
            tenant_id=t_id,
            actor="usr_testactor",
            action=action,
            detail={"step": action},
        )
        recorded.append(ev)

    # Fetch rows from DB in order of insertion
    with tenant_db_context(tenant_id=t_id):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT audit_id, at, actor, action, object_ref, matter_id, decision, detail, prev_hash, row_hash, seq
                FROM tpl.audit_event
                WHERE tenant_id = %s
                ORDER BY seq ASC
                """,
                [t_id],
            )
            rows = cursor.fetchall()

    assert len(rows) == len(actions)

    expected_prev = b"\x00" * 32
    for r in rows:
        (
            audit_id,
            at,
            actor,
            action,
            object_ref,
            matter_id,
            decision,
            detail_json,
            prev_hash,
            row_hash,
            seq,
        ) = r
        prev_hash_bytes = bytes(prev_hash)
        row_hash_bytes = bytes(row_hash)

        # Check prev_hash links to prior row_hash
        assert prev_hash_bytes == expected_prev

        # Recompute hash
        detail = json.loads(detail_json) if isinstance(detail_json, str) else detail_json
        payload = {
            "action": action,
            "actor": actor,
            "at": at.isoformat(),
            "audit_id": audit_id,
            "decision": decision,
            "detail": detail,
            "matter_id": matter_id,
            "object_ref": object_ref,
            "seq": seq,
            "tenant_id": t_id,
        }
        canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        hasher = hashlib.sha256()
        hasher.update(prev_hash_bytes)
        hasher.update(canonical_bytes)
        assert hasher.digest() == row_hash_bytes

        expected_prev = row_hash_bytes


def test_audit_event_truly_append_only_under_app_rw(audit_tenant: Tenant) -> None:
    """Directive #6: Attempting raw SQL UPDATE or DELETE on tpl.audit_event raises an error."""
    t_id = audit_tenant.tenant_id
    ev = record_audit_event(
        tenant_id=t_id,
        actor="usr_testactor",
        action="TEST_ACTION",
    )

    # 1. Under app_rw role (or trigger under owner), UPDATE is forbidden
    with tenant_db_context(tenant_id=t_id):
        with connection.cursor() as cursor:
            with pytest.raises(Exception) as exc_info:
                with transaction.atomic():
                    cursor.execute(
                        "UPDATE tpl.audit_event SET action = 'MUTATED' WHERE audit_id = %s",
                        [ev.audit_id],
                    )
            err_msg = str(exc_info.value).lower()
            assert (
                "permission denied" in err_msg
                or "cannot update or delete" in err_msg
                or "immutable" in err_msg
                or "append-only" in err_msg
                or "strictly forbidden" in err_msg
            )

    # 2. Under app_rw role (or trigger under owner), DELETE is forbidden
    with tenant_db_context(tenant_id=t_id):
        with connection.cursor() as cursor:
            with pytest.raises(Exception) as exc_info:
                with transaction.atomic():
                    cursor.execute(
                        "DELETE FROM tpl.audit_event WHERE audit_id = %s",
                        [ev.audit_id],
                    )
            err_msg = str(exc_info.value).lower()
            assert (
                "permission denied" in err_msg
                or "cannot update or delete" in err_msg
                or "immutable" in err_msg
                or "append-only" in err_msg
                or "strictly forbidden" in err_msg
            )

    # 3. Even as table owner/superuser, the trigger forbids UPDATE or DELETE
    with connections["owner"].cursor() as cursor:
        with pytest.raises(Exception) as exc_info:
            with transaction.atomic(using="owner"):
                cursor.execute(
                    "UPDATE tpl.audit_event SET action = 'TAMPERED' WHERE audit_id = %s",
                    [ev.audit_id],
                )
        assert "strictly forbidden" in str(exc_info.value).lower()


def test_audit_concurrent_inserts_serialize_without_forks(audit_tenant: Tenant) -> None:
    """Directive #6: Concurrent audit event insertions serialize per tenant without chain forks."""
    t_id = audit_tenant.tenant_id
    num_threads = 4
    events_per_thread = 5
    total_events = num_threads * events_per_thread

    def worker_insert(thread_idx: int) -> None:
        for i in range(events_per_thread):
            record_audit_event(
                tenant_id=t_id,
                actor=f"usr_worker_{thread_idx}",
                action=f"ACTION_{thread_idx}_{i}",
                detail={"thread": thread_idx, "iter": i},
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker_insert, idx) for idx in range(num_threads)]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    # Now verify the chain integrity across all inserted events
    with tenant_db_context(tenant_id=t_id):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT audit_id, prev_hash, row_hash
                FROM tpl.audit_event
                WHERE tenant_id = %s
                """,
                [t_id],
            )
            rows = cursor.fetchall()

    assert len(rows) == total_events

    # Verify no two rows share the same prev_hash (which would mean a fork!)
    # Except that only the genesis block has b"\x00"*32
    prev_hashes = [bytes(r[1]) for r in rows]
    genesis_count = prev_hashes.count(b"\x00" * 32)
    assert genesis_count == 1, (
        f"Expected exactly 1 genesis link, found {genesis_count} forks at genesis!"
    )

    non_genesis_prev = [h for h in prev_hashes if h != b"\x00" * 32]
    assert len(non_genesis_prev) == len(set(non_genesis_prev)), (
        "Detected forked prev_hash in audit chain!"
    )

    # Verify full linear chain connects from tail to head
    row_hash_to_prev = {bytes(r[2]): bytes(r[1]) for r in rows}
    all_row_hashes = set(row_hash_to_prev.keys())

    # The head of the chain is the row_hash that is not referenced by any other row's prev_hash
    head_candidates = [h for h in all_row_hashes if h not in prev_hashes]
    assert len(head_candidates) == 1, f"Expected exactly 1 chain head, found {len(head_candidates)}"

    curr = head_candidates[0]
    visited_count = 0
    while curr != b"\x00" * 32:
        visited_count += 1
        curr = row_hash_to_prev[curr]

    assert visited_count == total_events, (
        f"Chain traversal reached {visited_count} events instead of {total_events}"
    )


def test_verify_chain_on_valid_log(audit_tenant: Tenant) -> None:
    """verify_chain returns (True, None) on a clean, valid hash-chained audit log."""
    t_id = audit_tenant.tenant_id
    for i in range(5):
        record_audit_event(
            tenant_id=t_id,
            actor="usr_actor",
            action=f"ACTION_{i}",
            detail={"count": i},
        )

    is_valid, err = verify_chain(t_id)
    assert is_valid is True
    assert err is None


def test_verify_chain_detects_payload_tampering(audit_tenant: Tenant) -> None:
    """verify_chain detects payload alteration (hash mismatch)."""
    t_id = audit_tenant.tenant_id
    for i in range(3):
        record_audit_event(
            tenant_id=t_id,
            actor="usr_actor",
            action=f"ACTION_{i}",
        )

    # Disable trigger temporarily to simulate malicious raw DB tamper
    with connections["owner"].cursor() as cursor:
        cursor.execute("ALTER TABLE tpl.audit_event DISABLE TRIGGER audit_event_append_only;")
        try:
            cursor.execute(
                "UPDATE tpl.audit_event SET action = 'TAMPERED_ACTION' WHERE tenant_id = %s AND seq = 2;",
                [t_id],
            )
        finally:
            cursor.execute("ALTER TABLE tpl.audit_event ENABLE TRIGGER audit_event_append_only;")

    is_valid, err = verify_chain(t_id)
    assert is_valid is False
    assert err is not None
    assert "Hash mismatch" in err


def test_verify_chain_detects_broken_hash_link(audit_tenant: Tenant) -> None:
    """verify_chain detects broken prev_hash links between successive records."""
    t_id = audit_tenant.tenant_id
    for i in range(3):
        record_audit_event(
            tenant_id=t_id,
            actor="usr_actor",
            action=f"ACTION_{i}",
        )

    # Disable trigger temporarily to tamper with prev_hash
    with connections["owner"].cursor() as cursor:
        cursor.execute("ALTER TABLE tpl.audit_event DISABLE TRIGGER audit_event_append_only;")
        try:
            cursor.execute(
                "UPDATE tpl.audit_event SET prev_hash = %s WHERE tenant_id = %s AND seq = 2;",
                [b"\xff" * 32, t_id],
            )
        finally:
            cursor.execute("ALTER TABLE tpl.audit_event ENABLE TRIGGER audit_event_append_only;")

    is_valid, err = verify_chain(t_id)
    assert is_valid is False
    assert err is not None
    assert "Broken hash chain" in err
