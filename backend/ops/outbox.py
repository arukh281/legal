"""Transactional outbox publisher, dispatcher, and consumer inbox delivery.

Complies with docs/mvp/03_data_model_and_contracts.md §4 and docs/01_master_architecture.md §6.1-6.2.
"""

import hashlib
import json
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import structlog
from django.db import connection, transaction

logger = structlog.get_logger(__name__)

# Registry for consumer event handlers: (consumer, event_type) -> callable
HANDLER_REGISTRY: dict[tuple[str, str], Callable[..., Any]] = {}


def register_handler(
    consumer: str, event_type: str
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register a consumer event handler."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        HANDLER_REGISTRY[(consumer, event_type)] = fn
        return fn

    return decorator


def canonical_json_bytes(data: Any) -> bytes:
    """Serialize data to deterministic JSON bytes."""
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def generate_ulid_string() -> str:
    """Generate a 26-char Crockford ULID placeholder for S01."""
    # S01 uses timestamp + random hex formatted as 26-char string
    timestamp_ms = int(time.time() * 1000)
    rand_part = uuid.uuid4().hex[:16]
    return f"{timestamp_ms:010x}{rand_part}".upper()[:26]


def publish_event(
    *,
    event_type: str,
    source: str,
    subject: str | None = None,
    dataschema: str,
    dataclass: str,
    idempotencykey: str,
    schemaversion: str,
    data: dict[str, Any],
    topic: str,
    partition_key: str,
    tenantid: str | None = None,
    traceparent: str | None = None,
    causationid: str | None = None,
    datasig: str | None = None,
    lane: str | None = "rt",
    event_id: str | None = None,
    now: datetime | None = None,
) -> str:
    """Insert an event into ops.event_outbox in the caller's transaction and notify.

    Enforces CloudEvents 1.0 envelope + D2 rules (E1-E4, E7).
    """
    if event_id is None:
        event_id = generate_ulid_string()

    if now is None:
        now = datetime.now(UTC)

    # Perform SQL insert within current transaction
    sql = """
    INSERT INTO ops.event_outbox (
        id, specversion, type, source, time, subject, datacontenttype,
        dataschema, tenantid, dataclass, traceparent, causationid,
        idempotencykey, schemaversion, datasig, data, topic, partition_key,
        lane, created_at, dispatched_at
    ) VALUES (
        %s, '1.0', %s, %s, %s, %s, 'application/json',
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s::jsonb, %s, %s,
        %s, %s, NULL
    );
    """
    json_data = json.dumps(data)

    with connection.cursor() as cursor:
        cursor.execute(
            sql,
            [
                event_id,
                event_type,
                source,
                now,
                subject,
                dataschema,
                tenantid,
                dataclass,
                traceparent,
                causationid,
                idempotencykey,
                schemaversion,
                datasig,
                json_data,
                topic,
                partition_key,
                lane,
                now,
            ],
        )
        # Notify listeners on the 'outbox' channel with the topic
        cursor.execute("SELECT pg_notify('outbox', %s);", [topic])

    logger.info(
        "outbox_event_published",
        event_id=event_id,
        event_type=event_type,
        topic=topic,
        partition_key=partition_key,
        dataclass=dataclass,
        tenantid=tenantid,
    )

    return event_id


def dispatch_pending_events(batch_size: int = 100) -> list[str]:
    """Fetch pending outbox events using SKIP LOCKED and defer deliveries.

    Returns the list of dispatched event IDs.
    """
    dispatched_ids: list[str] = []

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, type, source, topic, partition_key, lane, data, tenantid, dataclass
                FROM ops.event_outbox
                WHERE dispatched_at IS NULL
                ORDER BY created_at ASC
                LIMIT %s
                FOR UPDATE SKIP LOCKED;
                """,
                [batch_size],
            )
            rows = cursor.fetchall()
            if not rows:
                return []

            # Fetch all active subscriptions
            cursor.execute(
                """
                SELECT consumer, type, handler, lane
                FROM ops.event_subscription
                WHERE enabled = true;
                """
            )
            sub_rows = cursor.fetchall()
            subs_by_type: dict[str, list[tuple[str, str | None]]] = {}
            for consumer, ev_type, _, lane in sub_rows:
                subs_by_type.setdefault(ev_type, []).append((consumer, lane))

            # Defer tasks for matching consumers
            for row in rows:
                ev_id, ev_type, ev_source, ev_topic, part_key, ev_lane, ev_data, ev_ten, ev_dc = row
                consumers = subs_by_type.get(ev_type, [])

                for consumer, sub_lane in consumers:
                    chosen_lane = ev_lane or sub_lane or "rt"
                    lock_key = f"{consumer}:{part_key}"
                    deliver_event.configure(
                        lock=lock_key,
                        queue=chosen_lane,
                    ).defer(
                        consumer=consumer,
                        source=ev_source,
                        event_id=ev_id,
                    )

                cursor.execute(
                    """
                    UPDATE ops.event_outbox
                    SET dispatched_at = now()
                    WHERE source = %s AND id = %s;
                    """,
                    [ev_source, ev_id],
                )
                dispatched_ids.append(ev_id)

    return dispatched_ids


def process_event_delivery(consumer: str, source: str, event_id: str) -> dict[str, Any]:
    """Execute consumer side-effect and inbox insert in ONE transaction (03 §4 step 3)."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, type, source, idempotencykey, data, topic, partition_key, tenantid
            FROM ops.event_outbox
            WHERE source = %s AND id = %s;
            """,
            [source, event_id],
        )
        row = cursor.fetchone()
        if not row:
            logger.error("outbox_event_not_found", source=source, event_id=event_id)
            return {"status": "ERROR", "reason": "EVENT_NOT_FOUND"}

        ev_id, ev_type, ev_source, idem_key, data, topic, part_key, ev_tenant_id = row

    payload_hash = hashlib.sha256(canonical_json_bytes(data)).digest()

    with transaction.atomic():
        with connection.cursor() as cursor:
            # Check event inbox
            cursor.execute(
                """
                SELECT payload_hash FROM ops.event_inbox
                WHERE consumer = %s AND idempotencykey = %s
                FOR UPDATE;
                """,
                [consumer, idem_key],
            )
            inbox_row = cursor.fetchone()

            if inbox_row is not None:
                existing_hash = bytes(inbox_row[0])
                if existing_hash == payload_hash:
                    # Duplicate key with SAME payload is a no-op
                    logger.info(
                        "inbox_duplicate_noop",
                        consumer=consumer,
                        idempotencykey=idem_key,
                        event_id=event_id,
                    )
                    return {"status": "NO_OP", "reason": "ALREADY_PROCESSED"}
                else:
                    # Duplicate key with DIFFERENT payload is parked as IDEMPOTENCY_KEY_REUSE
                    cursor.execute(
                        """
                        INSERT INTO ops.event_parked (consumer, event_id, reason, parked_at)
                        VALUES (%s, %s, 'IDEMPOTENCY_KEY_REUSE', now())
                        ON CONFLICT (consumer, event_id) DO UPDATE SET reason = EXCLUDED.reason;
                        """,
                        [consumer, event_id],
                    )
                    logger.warning(
                        "inbox_idempotency_key_reuse_parked",
                        consumer=consumer,
                        idempotencykey=idem_key,
                        event_id=event_id,
                    )
                    return {"status": "PARKED", "reason": "IDEMPOTENCY_KEY_REUSE"}

            # First time seeing this idempotency key for this consumer
            # 1. Execute consumer handler side-effect under tenant context (Directive #3)
            from workspace.db import tenant_db_context

            handler_fn = HANDLER_REGISTRY.get((consumer, ev_type))
            if handler_fn:
                with tenant_db_context(
                    tenant_id=ev_tenant_id,
                    user_id="outbox_consumer",
                    purpose="OUTBOX_CONSUMER",
                ):
                    handler_fn(
                        {
                            "id": ev_id,
                            "type": ev_type,
                            "source": ev_source,
                            "idempotencykey": idem_key,
                            "data": data,
                            "topic": topic,
                            "partition_key": part_key,
                        }
                    )

            # 2. Record in ops.event_inbox in the SAME transaction
            cursor.execute(
                """
                INSERT INTO ops.event_inbox (
                    consumer, idempotencykey, payload_hash, event_id, processed_at
                ) VALUES (%s, %s, %s, %s, now());
                """,
                [consumer, idem_key, payload_hash, event_id],
            )

    logger.info(
        "event_delivered_successfully",
        consumer=consumer,
        event_id=event_id,
        event_type=ev_type,
    )
    return {"status": "SUCCESS", "event_id": event_id}


# Procrastinate tasks
from procrastinate.contrib.django import app  # noqa: E402


@app.task(queue="dispatch", name="ops.outbox.dispatch_task")
def dispatch_task() -> list[str]:
    """Procrastinate task to dispatch pending outbox events.

    Implements 03 §4: reads pending rows FOR UPDATE SKIP LOCKED with a 2-second periodic sweep.
    """
    try:
        return dispatch_pending_events(batch_size=100)
    finally:
        try:
            dispatch_task.configure(
                queueing_lock="outbox_dispatcher",
                schedule_in={"seconds": 2},
            ).defer()
        except Exception:
            pass


@app.task(queue="rt", name="ops.outbox.deliver_event")
def deliver_event(consumer: str, source: str, event_id: str) -> dict[str, Any]:
    """Procrastinate task for per-consumer event delivery."""
    try:
        return process_event_delivery(consumer, source, event_id)
    except Exception as exc:
        logger.error(
            "deliver_event_failed",
            consumer=consumer,
            source=source,
            event_id=event_id,
            error=str(exc),
        )
        raise
