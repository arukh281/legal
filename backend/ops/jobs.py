"""Resumable multi-step job chains per docs/mvp/03_data_model_and_contracts.md §5.

Guarantees:
1. Atomic step completion: A step commits its output and defers the next step in ONE transaction.
2. Deterministic replay: If a step with the same step_key has status 'DONE', its output is reused.
3. Heartbeats and stalled-step reaper.
4. Signals for human-in-the-loop and external events.
"""

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import structlog
from django.db import connection, transaction

from ops.outbox import canonical_json_bytes, generate_ulid_string

logger = structlog.get_logger(__name__)

# Registry for step handlers: (chain_kind, step_name) -> callable
STEP_REGISTRY: dict[tuple[str, str], Callable[..., Any]] = {}
CHAIN_DEFINITIONS: dict[str, list[str]] = {}


def register_step(
    chain_kind: str, step_name: str
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register a step function in a job chain."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        STEP_REGISTRY[(chain_kind, step_name)] = fn
        steps = CHAIN_DEFINITIONS.setdefault(chain_kind, [])
        if step_name not in steps:
            steps.append(step_name)
        return fn

    return decorator


def compute_step_key(step: str, input_hashes: list[str], pipeline_version: str | None) -> str:
    """Compute deterministic step key: hash(step, input_hashes, pipeline_version)."""
    raw = f"{step}:" + ",".join(sorted(input_hashes)) + f":{pipeline_version or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_data_hash(data: Any) -> str:
    """Compute sha256 hash for any JSON-serializable data."""
    return hashlib.sha256(canonical_json_bytes(data)).hexdigest()


def start_job_chain(
    *,
    kind: str,
    idempotency_key: str,
    request: dict[str, Any],
    tenant_id: str | None = None,
    matter_id: str | None = None,
    budget: dict[str, Any] | None = None,
    pipeline_version: str | None = None,
    job_id: str | None = None,
) -> str:
    """Start or retrieve a job chain.

    If a chain with idempotency_key already exists, returns existing job_id.
    Otherwise creates job_chain and defers the first step.
    """
    if kind not in CHAIN_DEFINITIONS or not CHAIN_DEFINITIONS[kind]:
        raise ValueError(f"Unknown or empty job chain kind: {kind}")

    steps = CHAIN_DEFINITIONS[kind]
    first_step = steps[0]
    now = datetime.now(UTC)

    if job_id is None:
        job_id = f"job_{generate_ulid_string()}"

    if budget is None:
        budget = {"max_usd": 10.0, "max_steps": len(steps)}

    with transaction.atomic():
        with connection.cursor() as cursor:
            # Check for existing job by idempotency_key
            cursor.execute(
                "SELECT job_id, status FROM ops.job_chain WHERE idempotency_key = %s FOR UPDATE;",
                [idempotency_key],
            )
            existing = cursor.fetchone()
            if existing:
                logger.info(
                    "job_chain_already_exists",
                    job_id=existing[0],
                    status=existing[1],
                    idempotency_key=idempotency_key,
                )
                return str(existing[0])

            # Insert new job_chain
            cursor.execute(
                """
                INSERT INTO ops.job_chain (
                    job_id, kind, tenant_id, matter_id, idempotency_key,
                    status, request, budget, spent, current_step,
                    context_version, as_known_at, created_at, finished_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    'RUNNING', %s::jsonb, %s::jsonb, '{}'::jsonb, %s,
                    NULL, NULL, %s, NULL
                );
                """,
                [
                    job_id,
                    kind,
                    tenant_id,
                    matter_id,
                    idempotency_key,
                    json.dumps(request),
                    json.dumps(budget),
                    first_step,
                    now,
                ],
            )

            # Insert initial job_step
            input_hash = compute_data_hash(request)
            step_key = compute_step_key(first_step, [input_hash], pipeline_version)

            cursor.execute(
                """
                INSERT INTO ops.job_step (
                    job_id, step, attempt, status, step_key,
                    input_hashes, output, output_ref, pipeline_version,
                    procrastinate_job_id, heartbeat_at, started_at, finished_at, error
                ) VALUES (
                    %s, %s, 1, 'PENDING', %s,
                    %s, NULL, NULL, %s,
                    NULL, NULL, NULL, NULL, NULL
                );
                """,
                [job_id, first_step, step_key, [input_hash], pipeline_version],
            )

            # Defer initial step via Procrastinate on the same transaction
            execute_job_step.defer(job_id=job_id, step=first_step, attempt=1)

    logger.info("job_chain_started", job_id=job_id, kind=kind, first_step=first_step)
    return job_id


def run_step_logic(job_id: str, step: str, attempt: int) -> dict[str, Any]:
    """Execute the core logic of a step and manage atomic progression."""
    now = datetime.now(UTC)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT jc.kind, jc.request, jc.status, js.step_key, js.pipeline_version, js.input_hashes
            FROM ops.job_step js
            JOIN ops.job_chain jc ON js.job_id = jc.job_id
            WHERE js.job_id = %s AND js.step = %s AND js.attempt = %s;
            """,
            [job_id, step, attempt],
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Step record not found: {job_id}/{step} attempt {attempt}")

        kind, request_data, chain_status, step_key, pipeline_version, input_hashes = row

    if chain_status in ("CANCELLED", "FAILED"):
        logger.info("job_chain_aborted", job_id=job_id, status=chain_status)
        return {"status": "ABORTED", "chain_status": chain_status}

    # 1. Deterministic Replay Check: If a DONE step with this step_key already exists, reuse it!
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT output FROM ops.job_step
            WHERE job_id = %s AND step = %s AND status = 'DONE' AND step_key = %s
            ORDER BY attempt DESC LIMIT 1;
            """,
            [job_id, step, step_key],
        )
        replay_row = cursor.fetchone()

    if replay_row is not None:
        logger.info("job_step_replay_reused_output", job_id=job_id, step=step, step_key=step_key)
        raw_output = replay_row[0]
        step_output = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
        replayed = True
    else:
        replayed = False
        # Mark as RUNNING and heartbeat
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE ops.job_step
                SET status = 'RUNNING', started_at = %s, heartbeat_at = %s
                WHERE job_id = %s AND step = %s AND attempt = %s;
                """,
                [now, now, job_id, step, attempt],
            )

        # Retrieve outputs of preceding steps
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT step, output FROM ops.job_step
                WHERE job_id = %s AND status = 'DONE';
                """,
                [job_id],
            )
            prior_outputs = {
                r[0]: (json.loads(r[1]) if isinstance(r[1], str) else r[1])
                for r in cursor.fetchall()
            }

        step_fn = STEP_REGISTRY.get((kind, step))
        if not step_fn:
            raise ValueError(f"No handler registered for ({kind}, {step})")

        # Execute step function
        context = {
            "job_id": job_id,
            "step": step,
            "attempt": attempt,
            "request": request_data,
            "pipeline_version": pipeline_version,
            "prior_outputs": prior_outputs,
        }
        step_output = step_fn(context)

    # 2. In ONE transaction: commit current step output and defer next step
    steps = CHAIN_DEFINITIONS.get(kind, [])
    current_idx = steps.index(step)
    has_next = current_idx + 1 < len(steps)
    next_step = steps[current_idx + 1] if has_next else None
    finish_time = datetime.now(UTC)

    with transaction.atomic():
        with connection.cursor() as cursor:
            # Mark current step DONE
            cursor.execute(
                """
                UPDATE ops.job_step
                SET status = 'DONE', output = %s::jsonb, finished_at = %s
                WHERE job_id = %s AND step = %s AND attempt = %s;
                """,
                [json.dumps(step_output), finish_time, job_id, step, attempt],
            )

            if has_next and next_step:
                # Insert next step as PENDING
                next_input_hash = compute_data_hash(step_output)
                next_step_key = compute_step_key(next_step, [next_input_hash], pipeline_version)

                cursor.execute(
                    """
                    INSERT INTO ops.job_step (
                        job_id, step, attempt, status, step_key,
                        input_hashes, output, output_ref, pipeline_version,
                        procrastinate_job_id, heartbeat_at, started_at, finished_at, error
                    ) VALUES (
                        %s, %s, 1, 'PENDING', %s,
                        %s, NULL, NULL, %s,
                        NULL, NULL, NULL, NULL, NULL
                    ) ON CONFLICT (job_id, step, attempt) DO NOTHING;
                    """,
                    [job_id, next_step, next_step_key, [next_input_hash], pipeline_version],
                )

                # Update current_step on chain
                cursor.execute(
                    """
                    UPDATE ops.job_chain
                    SET current_step = %s
                    WHERE job_id = %s;
                    """,
                    [next_step, job_id],
                )

                # Defer next step execution
                execute_job_step.defer(job_id=job_id, step=next_step, attempt=1)
            else:
                # Last step: mark chain PUBLISHED
                cursor.execute(
                    """
                    UPDATE ops.job_chain
                    SET status = 'PUBLISHED', finished_at = %s, current_step = NULL
                    WHERE job_id = %s;
                    """,
                    [finish_time, job_id],
                )

    logger.info(
        "job_step_completed",
        job_id=job_id,
        step=step,
        attempt=attempt,
        has_next=has_next,
        replayed=replayed,
    )
    return {"status": "DONE", "job_id": job_id, "step": step, "output": step_output}


def heartbeat_step(job_id: str, step: str, attempt: int) -> None:
    """Update heartbeat timestamp for a running step."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE ops.job_step
            SET heartbeat_at = now()
            WHERE job_id = %s AND step = %s AND attempt = %s AND status = 'RUNNING';
            """,
            [job_id, step, attempt],
        )


def reap_stalled_steps(stalled_threshold_seconds: int = 90) -> list[dict[str, Any]]:
    """Find RUNNING steps with stale heartbeats and retry or fail them."""
    reaped: list[dict[str, Any]] = []

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT js.job_id, js.step, js.attempt, js.step_key, js.input_hashes, js.pipeline_version
                FROM ops.job_step js
                JOIN ops.job_chain jc ON js.job_id = jc.job_id
                WHERE js.status = 'RUNNING'
                  AND jc.status = 'RUNNING'
                  AND (js.heartbeat_at < now() - make_interval(secs => %s)
                       OR (js.heartbeat_at IS NULL AND js.started_at < now() - make_interval(secs => %s)))
                FOR UPDATE SKIP LOCKED;
                """,
                [stalled_threshold_seconds, stalled_threshold_seconds],
            )
            rows = cursor.fetchall()

            for job_id, step, attempt, step_key, input_hashes, pipeline_version in rows:
                if attempt < 3:
                    # Increment attempt and re-defer
                    cursor.execute(
                        """
                        UPDATE ops.job_step
                        SET status = 'FAILED', error = '{\"reason\": \"STALLED_HEARTBEAT\"}'::jsonb
                        WHERE job_id = %s AND step = %s AND attempt = %s;
                        """,
                        [job_id, step, attempt],
                    )

                    new_attempt = attempt + 1
                    cursor.execute(
                        """
                        INSERT INTO ops.job_step (
                            job_id, step, attempt, status, step_key,
                            input_hashes, output, output_ref, pipeline_version,
                            procrastinate_job_id, heartbeat_at, started_at, finished_at, error
                        ) VALUES (
                            %s, %s, %s, 'PENDING', %s,
                            %s, NULL, NULL, %s,
                            NULL, NULL, NULL, NULL, NULL
                        );
                        """,
                        [job_id, step, new_attempt, step_key, input_hashes, pipeline_version],
                    )

                    execute_job_step.defer(job_id=job_id, step=step, attempt=new_attempt)
                    reaped.append({"job_id": job_id, "step": step, "retried_attempt": new_attempt})
                    logger.warning(
                        "stalled_step_reaped_retried", job_id=job_id, step=step, attempt=new_attempt
                    )
                else:
                    # Exceeded max attempts, fail step and chain
                    cursor.execute(
                        """
                        UPDATE ops.job_step
                        SET status = 'FAILED', error = '{\"reason\": \"MAX_ATTEMPTS_EXCEEDED_AFTER_STALL\"}'::jsonb
                        WHERE job_id = %s AND step = %s AND attempt = %s;
                        """,
                        [job_id, step, attempt],
                    )
                    cursor.execute(
                        """
                        UPDATE ops.job_chain
                        SET status = 'FAILED', finished_at = now()
                        WHERE job_id = %s;
                        """,
                        [job_id],
                    )
                    reaped.append({"job_id": job_id, "step": step, "failed": True})
                    logger.error("stalled_step_reaped_failed", job_id=job_id, step=step)

    return reaped


def send_job_signal(job_id: str, signal: str, payload: dict[str, Any]) -> None:
    """Send a signal to a job chain."""
    allowed_signals = {"confirm_dates", "confirm_issues", "approve_draft", "cancel"}
    if signal not in allowed_signals:
        raise ValueError(f"Signal '{signal}' not in allowed set: {allowed_signals}")

    now = datetime.now(UTC)
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ops.job_signal (job_id, signal, payload, received_at, consumed_at)
                VALUES (%s, %s, %s::jsonb, %s, NULL);
                """,
                [job_id, signal, json.dumps(payload), now],
            )
            if signal == "cancel":
                cursor.execute(
                    """
                    UPDATE ops.job_chain
                    SET status = 'CANCELLED', finished_at = now()
                    WHERE job_id = %s;
                    """,
                    [job_id],
                )
    logger.info("job_signal_received", job_id=job_id, signal=signal)


# Procrastinate tasks
from procrastinate.contrib.django import app  # noqa: E402


@app.task(queue="rt", name="ops.jobs.execute_job_step")
def execute_job_step(job_id: str, step: str, attempt: int = 1) -> dict[str, Any]:
    """Procrastinate task to execute a job step."""
    return run_step_logic(job_id=job_id, step=step, attempt=attempt)


@app.task(queue="bulk", name="ops.jobs.reaper_task")
def reaper_task() -> list[dict[str, Any]]:
    """Procrastinate periodic task to reap stalled steps."""
    return reap_stalled_steps()
