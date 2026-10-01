"""3-step demo chain for Session S01 exit check.

Per requirement #3:
- Does NOT emit doc.parsed.v1 (event names are contracts).
- Emits test-only event ops.demo.completed.v1 on topic plc.ops.demo.completed.v1.
- Kept isolated for validation and testing.
"""

from typing import Any

from ops.jobs import register_step
from ops.outbox import publish_event

DEMO_CHAIN_KIND = "DEMO_CHAIN"


@register_step(DEMO_CHAIN_KIND, "demo_step_one")
def demo_step_one(context: dict[str, Any]) -> dict[str, Any]:
    """Step 1: Ingest and validate test payload."""
    req = context.get("request", {})
    return {
        "step": "demo_step_one",
        "processed_text": req.get("text", "").upper(),
        "item_count": len(req.get("items", [])),
    }


@register_step(DEMO_CHAIN_KIND, "demo_step_two")
def demo_step_two(context: dict[str, Any]) -> dict[str, Any]:
    """Step 2: Aggregate and compute derived metrics."""
    prior = context.get("prior_outputs", {})
    step1_out = prior.get("demo_step_one", {})
    return {
        "step": "demo_step_two",
        "processed_text": step1_out.get("processed_text", ""),
        "item_count": step1_out.get("item_count", 0),
        "derived_score": step1_out.get("item_count", 0) * 10,
    }


@register_step(DEMO_CHAIN_KIND, "demo_step_three")
def demo_step_three(context: dict[str, Any]) -> dict[str, Any]:
    """Step 3: Finalize demo run and publish test-only event ops.demo.completed.v1."""
    prior = context.get("prior_outputs", {})
    step2_out = prior.get("demo_step_two", {})
    job_id = context["job_id"]

    final_payload = {
        "job_id": job_id,
        "score": step2_out.get("derived_score", 0),
        "status": "COMPLETED",
    }

    # Publish test-only event (per user requirement #3)
    publish_event(
        event_type="ops.demo.completed.v1",
        source="ops/demo@0.1.0",
        subject=job_id,
        dataschema="schemareg://ops/demo.completed.v1/1.0",
        dataclass="PUBLIC",
        idempotencykey=f"demo|complete|{job_id}",
        schemaversion="1.0",
        data=final_payload,
        topic="plc.ops.demo.completed.v1",
        partition_key=job_id,
        tenantid=None,
    )

    return {
        "step": "demo_step_three",
        "result": final_payload,
    }


# Crash recovery test chain (for test_job_chain_crash_recovery_killing_real_worker_process)
CRASH_CHAIN_KIND = "CRASH_CHAIN"
CRASH_SYNC_FILE = "/tmp/step_b_started.tmp"


@register_step(CRASH_CHAIN_KIND, "crash_step_a")
def crash_step_a(context: dict[str, Any]) -> dict[str, Any]:
    return {"a": "done"}


@register_step(CRASH_CHAIN_KIND, "crash_step_b")
def crash_step_b(context: dict[str, Any]) -> dict[str, Any]:
    import time

    with open(CRASH_SYNC_FILE, "w") as f:
        f.write("started")
    time.sleep(5)
    return {"b": "done"}


@register_step(CRASH_CHAIN_KIND, "crash_step_c")
def crash_step_c(context: dict[str, Any]) -> dict[str, Any]:
    return {"c": "all_finished"}
