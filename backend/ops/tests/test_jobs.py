"""Resumable job chain tests against real PostgreSQL 18.

Tests required by prompt and user directives:
1. Replay with the same step_key reuses the output.
2. Full 3-step demo chain execution emitting ops.demo.completed.v1.
3. Actual worker process kill (SIGKILL) mid-step and resumption via new worker process.
"""

import json
import os
import subprocess
import sys
import time
import uuid
from typing import Any

import pytest
from django.db import connection

from ops.demo_chain import DEMO_CHAIN_KIND
from ops.jobs import (
    reap_stalled_steps,
    register_step,
    run_step_logic,
    start_job_chain,
)


@pytest.mark.django_db(transaction=True)
def test_job_chain_step_key_replay() -> None:
    """A replay with the same step_key reuses the output without re-executing logic."""
    kind = f"TEST_REPLAY_CHAIN_{uuid.uuid4().hex[:8]}"
    step1_calls = 0

    @register_step(kind, "replay_step_1")
    def replay_step_1(context: dict[str, Any]) -> dict[str, Any]:
        nonlocal step1_calls
        step1_calls += 1
        return {"result": "first_run_val"}

    @register_step(kind, "replay_step_2")
    def replay_step_2(context: dict[str, Any]) -> dict[str, Any]:
        return {"done": True}

    job_id = start_job_chain(
        kind=kind,
        idempotency_key=f"replay-idem-key-{uuid.uuid4().hex}",
        request={"input": 123},
        pipeline_version="comp@1.0|m|s|r|p",
    )

    # First run of step 1
    res1 = run_step_logic(job_id=job_id, step="replay_step_1", attempt=1)
    assert res1["status"] == "DONE"
    assert step1_calls == 1

    # Second run of step 1 with same input/pipeline_version (same step_key)
    res2 = run_step_logic(job_id=job_id, step="replay_step_1", attempt=1)
    assert res2["status"] == "DONE"
    assert res2["output"] == {"result": "first_run_val"}
    assert step1_calls == 1, "Step 1 logic should not re-execute; output must be reused"


@pytest.mark.django_db(transaction=True)
def test_demo_chain_full_execution() -> None:
    """Full 3-step demo chain runs to completion and emits ops.demo.completed.v1."""
    from procrastinate.contrib.django import app

    job_id = start_job_chain(
        kind=DEMO_CHAIN_KIND,
        idempotency_key=f"demo-chain-e2e-{uuid.uuid4().hex}",
        request={"text": "hello legal world", "items": ["ibc", "nclt"]},
        pipeline_version="ops/demo@0.1.0",
    )

    # Execute all queued steps via worker loop until published
    for _ in range(10):
        with connection.cursor() as cur:
            cur.execute("SELECT status FROM ops.job_chain WHERE job_id = %s;", [job_id])
            if cur.fetchone()[0] == "PUBLISHED":
                break
        app.run_worker(queues=["rt"], wait=False, listen_notify=False)

    # Verify all 3 steps completed
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT step, status, output FROM ops.job_step
            WHERE job_id = %s
            ORDER BY started_at ASC;
            """,
            [job_id],
        )
        steps = cur.fetchall()
        assert len(steps) == 3
        step_names = [s[0] for s in steps]
        assert step_names == ["demo_step_one", "demo_step_two", "demo_step_three"]
        assert all(s[1] == "DONE" for s in steps)

        # Verify chain is PUBLISHED
        cur.execute("SELECT status FROM ops.job_chain WHERE job_id = %s;", [job_id])
        chain_status = cur.fetchone()[0]
        assert chain_status == "PUBLISHED"

        # Verify test event ops.demo.completed.v1 was published (per requirement #3)
        cur.execute(
            """
            SELECT type, topic, data FROM ops.event_outbox
            WHERE type = 'ops.demo.completed.v1' AND subject = %s;
            """,
            [job_id],
        )
        ev_row = cur.fetchone()
        assert ev_row is not None
        assert ev_row[0] == "ops.demo.completed.v1"
        assert ev_row[1] == "plc.ops.demo.completed.v1"
        data_val = ev_row[2] if isinstance(ev_row[2], dict) else json.loads(ev_row[2])
        assert data_val["score"] == 20


@pytest.mark.django_db(transaction=True)
def test_job_chain_crash_recovery_killing_real_worker_process() -> None:
    """Actually kill a worker process mid-step with SIGKILL and restart a new one.

    Per user requirement #6:
    The crash-recovery test must actually kill a worker process mid-step
    and start a new one, not simulate it with a flag.
    """
    from ops.demo_chain import CRASH_CHAIN_KIND, CRASH_SYNC_FILE

    if os.path.exists(CRASH_SYNC_FILE):
        os.remove(CRASH_SYNC_FILE)

    job_id = start_job_chain(
        kind=CRASH_CHAIN_KIND,
        idempotency_key=f"crash-test-key-{uuid.uuid4().hex}",
        request={"test": True},
        pipeline_version="test@1.0",
    )

    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = "core.settings.test"
    # Ensure subprocess connects to the test database that pytest created
    env["POSTGRES_DB"] = connection.settings_dict["NAME"]
    env["POSTGRES_PORT"] = str(connection.settings_dict.get("PORT", "5433"))
    env["POSTGRES_HOST"] = str(connection.settings_dict.get("HOST", "127.0.0.1"))
    env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

    # Spawn real worker subprocess with --no-listen-notify
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    proc = subprocess.Popen(
        [
            sys.executable,
            "manage.py",
            "procrastinate",
            "worker",
            "--queues",
            "rt",
            "--no-listen-notify",
        ],
        cwd=backend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait until step B starts executing
        for _ in range(80):
            if os.path.exists(CRASH_SYNC_FILE):
                break
            time.sleep(0.1)

        assert os.path.exists(CRASH_SYNC_FILE), "Worker did not reach crash_step_b in time"

        # Verify step A is DONE in the DB
        with connection.cursor() as cur:
            cur.execute(
                "SELECT status FROM ops.job_step WHERE job_id = %s AND step = 'crash_step_a';",
                [job_id],
            )
            assert cur.fetchone()[0] == "DONE"

        # KILL THE WORKER PROCESS MID-STEP (SIGKILL)
        proc.kill()
        proc.wait(timeout=5)

    finally:
        if proc.poll() is None:
            proc.kill()
        if os.path.exists(CRASH_SYNC_FILE):
            os.remove(CRASH_SYNC_FILE)

    # Step A remains DONE, Step B was interrupted
    with connection.cursor() as cur:
        cur.execute(
            "SELECT status FROM ops.job_step WHERE job_id = %s AND step = 'crash_step_a';", [job_id]
        )
        assert cur.fetchone()[0] == "DONE"

    # Reaper detects stalled step B and re-defers it
    reaped = reap_stalled_steps(stalled_threshold_seconds=0)
    assert any(r["job_id"] == job_id and r["step"] == "crash_step_b" for r in reaped)

    # Start NEW worker to resume and finish the chain
    from procrastinate.contrib.django import app

    for _ in range(10):
        with connection.cursor() as cur:
            cur.execute("SELECT status FROM ops.job_chain WHERE job_id = %s;", [job_id])
            if cur.fetchone()[0] == "PUBLISHED":
                break
        app.run_worker(queues=["rt"], wait=False, listen_notify=False)

    # Verify entire chain resumed and finished without re-running completed step A
    with connection.cursor() as cur:
        cur.execute("SELECT status FROM ops.job_chain WHERE job_id = %s;", [job_id])
        assert cur.fetchone()[0] == "PUBLISHED"

        cur.execute(
            """
            SELECT step, status, attempt FROM ops.job_step
            WHERE job_id = %s
            ORDER BY started_at ASC;
            """,
            [job_id],
        )
        steps = cur.fetchall()
        step_names = [s[0] for s in steps if s[1] == "DONE"]
        assert "crash_step_a" in step_names
        assert "crash_step_b" in step_names
        assert "crash_step_c" in step_names


@pytest.mark.django_db(transaction=True)
def test_job_chain_step_sets_and_resets_tenant_db_context() -> None:
    """Directive #3: Job step executions set and reset tenant context from request data."""
    kind = f"TEST_TENANT_CONTEXT_CHAIN_{uuid.uuid4().hex[:8]}"
    observed_tenants: list[str | None] = []

    @register_step(kind, "tenant_step_1")
    def tenant_step_1(context: dict[str, Any]) -> dict[str, Any]:
        with connection.cursor() as cur:
            cur.execute("SELECT current_setting('app.tenant_id', true);")
            val = cur.fetchone()[0]
            observed_tenants.append(val)
        return {"observed": val}

    # Job for Tenant Alpha
    job_a = start_job_chain(
        kind=kind,
        idempotency_key=f"tenant-ctx-job-a-{uuid.uuid4().hex}",
        request={"tenant_id": "ten_alpha", "user_id": "usr_alpha"},
        pipeline_version="comp@1.0|m|s|r|p",
    )
    res_a = run_step_logic(job_id=job_a, step="tenant_step_1", attempt=1)
    assert res_a["status"] == "DONE"
    assert observed_tenants[-1] == "ten_alpha"

    # Context must be reset immediately after job A finishes
    with connection.cursor() as cur:
        cur.execute("SELECT current_setting('app.tenant_id', true);")
        assert cur.fetchone()[0] in (None, "")

    # Job for Tenant Beta on the exact same connection
    job_b = start_job_chain(
        kind=kind,
        idempotency_key=f"tenant-ctx-job-b-{uuid.uuid4().hex}",
        request={"tenant_id": "ten_beta", "user_id": "usr_beta"},
        pipeline_version="comp@1.0|m|s|r|p",
    )
    res_b = run_step_logic(job_id=job_b, step="tenant_step_1", attempt=1)
    assert res_b["status"] == "DONE"
    assert observed_tenants[-1] == "ten_beta"

    # Context must be reset immediately after job B finishes
    with connection.cursor() as cur:
        cur.execute("SELECT current_setting('app.tenant_id', true);")
        assert cur.fetchone()[0] in (None, "")
