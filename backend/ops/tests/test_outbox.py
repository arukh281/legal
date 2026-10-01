"""Outbox and Inbox tests against real PostgreSQL 18.

Tests required by prompt and user directives:
1. An event and its state change commit or roll back together.
2. A duplicate idempotency key with the same payload is a no-op.
3. With a different payload it is parked (IDEMPOTENCY_KEY_REUSE).
4. Per-partition-key ordering holds with 2 workers.
5. Outbox CHECKs reject a PUBLIC event with a tenantid.
6. Outbox CHECKs reject a topic that doesn't match its tenant.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from django.db import IntegrityError, connection, transaction

from ops.outbox import (
    HANDLER_REGISTRY,
    process_event_delivery,
    publish_event,
)


@pytest.mark.django_db(transaction=True)
def test_outbox_atomicity_commit() -> None:
    """An event and state change commit together inside a transaction."""
    pv_id = "test.comp@1.0.0|mod|snap|us-east|prompt"

    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ops.pipeline_version (
                    pipeline_version, component, semver, code_sha
                ) VALUES (%s, 'test.comp', '1.0.0', 'sha256:123')
                ON CONFLICT (pipeline_version) DO NOTHING;
                """,
                [pv_id],
            )
        ev_id = publish_event(
            event_type="test.event.v1",
            source="test/source@1.0.0",
            dataschema="schemareg://test/event.v1",
            dataclass="PUBLIC",
            idempotencykey="atomicity-commit-1",
            schemaversion="1.0",
            data={"status": "committed"},
            topic="plc.test.event.v1",
            partition_key="pk-1",
            tenantid=None,
        )

    with connection.cursor() as cur:
        cur.execute(
            "SELECT pipeline_version FROM ops.pipeline_version WHERE pipeline_version = %s;",
            [pv_id],
        )
        assert cur.fetchone() is not None
        cur.execute("SELECT id FROM ops.event_outbox WHERE id = %s;", [ev_id])
        assert cur.fetchone() is not None


@pytest.mark.django_db(transaction=True)
def test_outbox_atomicity_rollback() -> None:
    """An event and state change roll back together if an exception occurs."""
    idem_key = "atomicity-rollback-key-999"

    with pytest.raises(RuntimeError):
        with transaction.atomic():
            publish_event(
                event_type="test.event.v1",
                source="test/source@1.0.0",
                dataschema="schemareg://test/event.v1",
                dataclass="PUBLIC",
                idempotencykey=idem_key,
                schemaversion="1.0",
                data={"status": "rolling_back"},
                topic="plc.test.event.v1",
                partition_key="pk-rollback",
                tenantid=None,
            )
            raise RuntimeError("Forced rollback")

    with connection.cursor() as cur:
        cur.execute("SELECT id FROM ops.event_outbox WHERE idempotencykey = %s;", [idem_key])
        assert cur.fetchone() is None


@pytest.mark.django_db(transaction=True)
def test_inbox_idempotency_noop_same_payload() -> None:
    """A duplicate idempotency key with the same payload is a no-op."""
    consumer = "test_consumer_noop"
    ev_type = "test.idemp.v1"
    execution_count = 0

    def mock_handler(event: dict[str, Any]) -> None:
        nonlocal execution_count
        execution_count += 1

    HANDLER_REGISTRY[(consumer, ev_type)] = mock_handler

    ev_id = publish_event(
        event_type=ev_type,
        source="test/source@1.0.0",
        dataschema="schemareg://test/idemp.v1",
        dataclass="PUBLIC",
        idempotencykey="idem-key-same",
        schemaversion="1.0",
        data={"val": 42},
        topic="plc.test.idemp.v1",
        partition_key="pk-same",
        tenantid=None,
    )

    # First delivery: executes handler
    res1 = process_event_delivery(consumer, "test/source@1.0.0", ev_id)
    assert res1["status"] == "SUCCESS"
    assert execution_count == 1

    # Second delivery with SAME payload: no-op, handler not executed
    res2 = process_event_delivery(consumer, "test/source@1.0.0", ev_id)
    assert res2["status"] == "NO_OP"
    assert execution_count == 1


@pytest.mark.django_db(transaction=True)
def test_inbox_idempotency_parked_different_payload() -> None:
    """A duplicate idempotency key with a DIFFERENT payload is parked with IDEMPOTENCY_KEY_REUSE."""
    consumer = "test_consumer_park"
    ev_type = "test.idemp.v2"
    execution_count = 0

    def mock_handler(event: dict[str, Any]) -> None:
        nonlocal execution_count
        execution_count += 1

    HANDLER_REGISTRY[(consumer, ev_type)] = mock_handler

    # Event 1
    ev_id1 = publish_event(
        event_type=ev_type,
        source="test/source@1.0.0",
        dataschema="schemareg://test/idemp.v2",
        dataclass="PUBLIC",
        idempotencykey="reused-key-diff",
        schemaversion="1.0",
        data={"payload": "original"},
        topic="plc.test.idemp.v2",
        partition_key="pk-diff",
        tenantid=None,
    )

    res1 = process_event_delivery(consumer, "test/source@1.0.0", ev_id1)
    assert res1["status"] == "SUCCESS"
    assert execution_count == 1

    # Event 2 with SAME idempotency key but DIFFERENT data
    ev_id2 = publish_event(
        event_type=ev_type,
        source="test/source@1.0.0",
        dataschema="schemareg://test/idemp.v2",
        dataclass="PUBLIC",
        idempotencykey="reused-key-diff",
        schemaversion="1.0",
        data={"payload": "tampered_or_different"},
        topic="plc.test.idemp.v2",
        partition_key="pk-diff",
        tenantid=None,
    )

    res2 = process_event_delivery(consumer, "test/source@1.0.0", ev_id2)
    assert res2["status"] == "PARKED"
    assert res2["reason"] == "IDEMPOTENCY_KEY_REUSE"
    assert execution_count == 1  # Handler did not run for second event

    # Verify event is in ops.event_parked
    with connection.cursor() as cur:
        cur.execute(
            "SELECT reason FROM ops.event_parked WHERE consumer = %s AND event_id = %s;",
            [consumer, ev_id2],
        )
        row = cur.fetchone()
        assert row is not None
        assert row[0] == "IDEMPOTENCY_KEY_REUSE"


@pytest.mark.django_db(transaction=True)
def test_outbox_checks_reject_public_with_tenantid() -> None:
    """CHECK constraint rejects dataclass='PUBLIC' when tenantid is not NULL."""
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ops.event_outbox (
                        id, specversion, type, source, time, dataschema,
                        tenantid, dataclass, idempotencykey, schemaversion,
                        data, topic, partition_key
                    ) VALUES (
                        '01JTEST001', '1.0', 'test.ev.v1', 'src', now(), 'schema://test',
                        'ten_01JTEST', 'PUBLIC', 'idem-1', '1.0',
                        '{}'::jsonb, 'plc.test.ev.v1', 'pk1'
                    );
                    """
                )


@pytest.mark.django_db(transaction=True)
def test_outbox_checks_reject_tenant_with_plc_topic() -> None:
    """CHECK constraint rejects topic mismatch for tenant events."""
    # 1. tenantid is set, but topic is plc.*
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ops.event_outbox (
                        id, specversion, type, source, time, dataschema,
                        tenantid, dataclass, idempotencykey, schemaversion,
                        data, topic, partition_key
                    ) VALUES (
                        '01JTEST002', '1.0', 'test.ev.v1', 'src', now(), 'schema://test',
                        'ten_01JTEST', 'TENANT_CONFIDENTIAL', 'idem-2', '1.0',
                        '{}'::jsonb, 'plc.test.ev.v1', 'pk2'
                    );
                    """
                )

    # 2. tenantid is NULL, but topic is tpl.*
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ops.event_outbox (
                        id, specversion, type, source, time, dataschema,
                        tenantid, dataclass, idempotencykey, schemaversion,
                        data, topic, partition_key
                    ) VALUES (
                        '01JTEST003', '1.0', 'test.ev.v1', 'src', now(), 'schema://test',
                        NULL, 'PUBLIC', 'idem-3', '1.0',
                        '{}'::jsonb, 'tpl.ten_01JTEST.matter.alert.v1', 'pk3'
                    );
                    """
                )


@pytest.mark.django_db(transaction=True)
def test_partition_key_ordering_with_concurrent_workers() -> None:
    """Per-partition-key ordering holds across 2 workers using lock=consumer:partition_key."""
    from procrastinate.contrib.django import app

    consumer = "ordered_consumer"
    ev_type = "test.ordered.v1"
    partition_key = "matter_01J999"
    processed_sequence: list[int] = []

    def ordered_handler(event: dict[str, Any]) -> None:
        idx = event["data"]["seq"]
        processed_sequence.append(idx)

    HANDLER_REGISTRY[(consumer, ev_type)] = ordered_handler

    # Register subscription
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ops.event_subscription (consumer, type, handler, lane, enabled)
            VALUES (%s, %s, 'test_handler', 'rt', true)
            ON CONFLICT (consumer, type) DO UPDATE SET enabled = true;
            """,
            [consumer, ev_type],
        )

    # Clear any pending events from earlier tests
    with connection.cursor() as cur:
        cur.execute(
            "UPDATE ops.event_outbox SET dispatched_at = now() WHERE dispatched_at IS NULL;"
        )

    # Publish 5 events in strict sequence
    num_events = 5
    for i in range(num_events):
        publish_event(
            event_type=ev_type,
            source="test/ordered@1.0.0",
            dataschema="schemareg://test/ordered.v1",
            dataclass="PUBLIC",
            idempotencykey=f"ordered-key-{i}",
            schemaversion="1.0",
            data={"seq": i},
            topic="plc.test.ordered.v1",
            partition_key=partition_key,
            lane="rt",
            tenantid=None,
        )

    from ops.outbox import dispatch_pending_events

    dispatched = dispatch_pending_events(batch_size=100)
    assert len(dispatched) == num_events

    # Execute jobs using 2 concurrent worker threads with listen_notify=False
    def run_worker() -> None:
        try:
            app.run_worker(queues=["rt"], wait=False, listen_notify=False)
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(run_worker)
        f2 = executor.submit(run_worker)
        f1.result()
        f2.result()

    # Verify all 5 were processed strictly in order [0, 1, 2, 3, 4]
    assert processed_sequence == list(range(num_events)), (
        f"Partition key ordering violated: expected {list(range(num_events))}, got {processed_sequence}"
    )

    from django.db import connections

    connections.close_all()
