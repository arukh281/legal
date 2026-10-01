"""Tests for Model Gateway v0 runner, routing, residency, schema repair, metering, and privacy.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.15
- docs/mvp/04_stack_and_infra.md §2.8, §2.13
- docs/01a_spine_decision_record.md: D9, D14, D15
- Session S03 Directive #1 (unprefixed call_id), #8 (endpoint data_class_max >= call dataclass)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import pytest

from anchor_lib.ids import mint_id
from gateway.adapters.fake import FakeModelAdapter
from gateway.exceptions import (
    BudgetExhaustedError,
    NoQualifiedEndpointError,
    ResidencyFailClosedError,
    SchemaValidationError,
)
from gateway.models import LLMCallRecord, ModelEndpoint, ModelTaskContract
from gateway.runner import run, set_adapter_override
from workspace.authz import ExecutionContext


@pytest.fixture
def gateway_setup(db: None) -> dict[str, Any]:
    """Register sample ModelTaskContract and ModelEndpoints."""
    contract = ModelTaskContract.objects.create(
        task_id="extract_notice_parties",
        owner_phase="workspace",
        input_schema={
            "type": "object",
            "required": ["notice_text"],
            "properties": {"notice_text": {"type": "string"}},
        },
        output_schema={
            "type": "object",
            "required": ["claimant", "respondent", "amount_claimed"],
            "properties": {
                "claimant": {"type": "string"},
                "respondent": {"type": "string"},
                "amount_claimed": {"type": "number"},
            },
        },
        max_input_chars=10000,
        max_output_tokens=1000,
        data_class_max="PRIVILEGED",
        allowed_trust_labels=["CANONICAL", "PRIMARY"],
        tools_allowed=[],
        eval={"metric": "exact_match", "gold_set": "notices_v1"},
        determinism={"temperature": 0.0},
        prompt_variants={
            "default": "Extract parties from notice:\n{inputs}",
            "anthropic": "Extract parties from notice:\n{inputs}",
            "openai": "Extract parties from notice:\n{inputs}",
        },
        batch_ok=False,
    )

    ep_us = ModelEndpoint.objects.create(
        endpoint_id="anthropic-claude-3-5-sonnet-us",
        provider="anthropic",
        model_id="claude-3-5-sonnet-20241022",
        model_snapshot="20241022",
        processing_geo="US",
        storage_geo="US",
        zdr=True,
        data_class_max="PRIVILEGED",
        price={"in_per_mtok": 3.0, "out_per_mtok": 15.0, "cache_read_mult": 0.1},
        limits={"rpm": 1000, "tpm": 80000, "supports_batch": True},
        health="UP",
        qualified_tasks={"extract_notice_parties": True},
    )

    ep_in = ModelEndpoint.objects.create(
        endpoint_id="openai-gpt-4o-in",
        provider="openai",
        model_id="gpt-4o",
        model_snapshot="2024-08-06",
        processing_geo="IN",
        storage_geo="IN",
        zdr=True,
        data_class_max="PRIVILEGED",
        price={"in_per_mtok": 2.5, "out_per_mtok": 10.0, "cache_read_mult": 0.1},
        limits={"rpm": 1000, "tpm": 80000, "supports_batch": True},
        health="UP",
        qualified_tasks={"extract_notice_parties": True},
    )

    fake_anthropic = FakeModelAdapter()
    fake_openai = FakeModelAdapter()
    set_adapter_override("anthropic", fake_anthropic)
    set_adapter_override("openai", fake_openai)

    return {
        "contract": contract,
        "ep_us": ep_us,
        "ep_in": ep_in,
        "fake_anthropic": fake_anthropic,
        "fake_openai": fake_openai,
    }


def teardown_function() -> None:
    set_adapter_override("anthropic", None)
    set_adapter_override("openai", None)


def test_gateway_residency_in_only_fails_closed_when_no_in_endpoint(
    gateway_setup: dict[str, Any],
) -> None:
    """D15: If residency_policy is IN_ONLY and no IN endpoint is qualified, fail closed."""
    # Mark IN endpoint as DOWN
    ep_in = gateway_setup["ep_in"]
    ep_in.health = "DOWN"
    ep_in.save()

    ctx = ExecutionContext(
        tenant_id=mint_id("ten"),
        user_id=mint_id("usr"),
        firm_role="PARTNER",
        residency_policy="IN_ONLY",
    )

    with pytest.raises(ResidencyFailClosedError) as exc_info:
        run(
            task_id="extract_notice_parties",
            inputs={"notice_text": "Demand notice under IBC section 8..."},
            ctx=ctx,
        )

    assert "RESIDENCY_NO_QUALIFIED_ENDPOINT" in str(exc_info.value)


def test_gateway_residency_in_only_succeeds_with_in_endpoint(
    gateway_setup: dict[str, Any],
) -> None:
    """When an IN endpoint is UP, IN_ONLY successfully routes to it."""
    fake_openai: FakeModelAdapter = gateway_setup["fake_openai"]
    fake_openai.queue_response(
        json.dumps(
            {
                "claimant": "Operational Creditor Ltd",
                "respondent": "Corporate Debtor Pvt Ltd",
                "amount_claimed": 5000000.0,
            }
        )
    )

    ctx = ExecutionContext(
        tenant_id=mint_id("ten"),
        user_id=mint_id("usr"),
        firm_role="PARTNER",
        residency_policy="IN_ONLY",
    )

    result = run(
        task_id="extract_notice_parties",
        inputs={"notice_text": "Demand notice under IBC section 8..."},
        ctx=ctx,
    )

    assert result.call_record.processing_geo == "IN"
    assert result.call_record.endpoint_id == "openai-gpt-4o-in"
    assert result.output["claimant"] == "Operational Creditor Ltd"


def test_gateway_budget_exhaustion_stops_call(gateway_setup: dict[str, Any]) -> None:
    """Calls stop immediately if budget is already exhausted."""
    ctx = ExecutionContext(
        tenant_id=mint_id("ten"),
        user_id=mint_id("usr"),
        firm_role="PARTNER",
        llm_policy={"max_cost_usd": 10.0, "spent_usd": 10.5},
    )

    with pytest.raises(BudgetExhaustedError) as exc_info:
        run(
            task_id="extract_notice_parties",
            inputs={"notice_text": "Notice text..."},
            ctx=ctx,
        )

    assert "budget exhausted" in str(exc_info.value).lower()


def test_gateway_schema_validation_and_repair_flow(gateway_setup: dict[str, Any]) -> None:
    """Output schema repair: invalid response triggers 1 repair attempt with schema & error."""
    fake_anthropic: FakeModelAdapter = gateway_setup["fake_anthropic"]
    fake_openai: FakeModelAdapter = gateway_setup["fake_openai"]

    # 1st attempt: missing required key 'amount_claimed'
    bad_output = json.dumps({"claimant": "SBI", "respondent": "Essar Steel"})
    # 2nd attempt (repair): valid output
    repaired_output = json.dumps(
        {"claimant": "SBI", "respondent": "Essar Steel", "amount_claimed": 45000.0}
    )

    for adapter in (fake_anthropic, fake_openai):
        adapter.queue_response(bad_output)
        adapter.queue_response(repaired_output)

    ctx = ExecutionContext(
        tenant_id=mint_id("ten"),
        user_id=mint_id("usr"),
        firm_role="PARTNER",
        residency_policy="ANY",
    )

    result = run(
        task_id="extract_notice_parties",
        inputs={"notice_text": "Default on loan repayment..."},
        ctx=ctx,
    )

    assert result.attempts == 2
    assert result.call_record.repaired is True
    assert result.call_record.schema_valid is True
    assert result.output["amount_claimed"] == 45000.0

    # Both call records were stored in ops.llm_call_record
    records = list(
        LLMCallRecord.objects.filter(task_id="extract_notice_parties").order_by("created_at")
    )
    assert len(records) == 2
    rec1, rec2 = records[0], records[1]
    assert rec1.schema_valid is False
    assert rec1.repaired is False
    assert rec2.schema_valid is True
    assert rec2.repaired is True
    assert rec2.escalated_from == rec1.call_id

    # Directive #1: verify unprefixed 26-char Crockford ULID
    assert len(rec1.call_id) == 26
    assert not rec1.call_id.startswith("call_")


def test_gateway_schema_validation_fails_loudly_if_repair_fails(
    gateway_setup: dict[str, Any],
) -> None:
    """Repair fails loudly if 2nd attempt is also invalid."""
    fake_anthropic: FakeModelAdapter = gateway_setup["fake_anthropic"]

    # Both attempts invalid
    fake_anthropic.queue_response("Invalid non-json output")
    fake_anthropic.queue_response("Still invalid")

    ctx = ExecutionContext(
        tenant_id=mint_id("ten"),
        user_id=mint_id("usr"),
        firm_role="PARTNER",
        residency_policy="ANY",
    )

    with pytest.raises(SchemaValidationError) as exc_info:
        run(
            task_id="extract_notice_parties",
            inputs={"notice_text": "Notice..."},
            ctx=ctx,
        )

    assert "schema validation failed after repair" in str(exc_info.value).lower()


def test_directive_8_dataclass_enforcement_privileged_never_hits_public_max(
    gateway_setup: dict[str, Any],
) -> None:
    """Directive #8: endpoint routing must enforce endpoint.data_class_max >= call dataclass.

    A PRIVILEGED call must NEVER reach a PUBLIC-max endpoint.
    """
    # Create an endpoint that only allows PUBLIC data
    ModelEndpoint.objects.create(
        endpoint_id="public-only-endpoint",
        provider="anthropic",
        model_id="claude-3-haiku",
        model_snapshot="20240307",
        processing_geo="US",
        storage_geo="US",
        zdr=False,
        data_class_max="PUBLIC",
        price={"in_per_mtok": 0.25, "out_per_mtok": 1.25},
        limits={"rpm": 1000, "tpm": 80000},
        health="UP",
        qualified_tasks={"extract_notice_parties": True},
    )

    # Disable all PRIVILEGED endpoints
    ModelEndpoint.objects.filter(data_class_max="PRIVILEGED").update(health="DOWN")

    # PRIVILEGED call
    ctx = ExecutionContext(
        tenant_id=mint_id("ten"),
        user_id=mint_id("usr"),
        firm_role="PARTNER",
        dataclass="PRIVILEGED",
    )

    # Must refuse to route to public-only-endpoint
    with pytest.raises(NoQualifiedEndpointError):
        run(
            task_id="extract_notice_parties",
            inputs={"notice_text": "Extremely sensitive legal notice"},
            ctx=ctx,
        )


def test_privacy_never_logs_confidential_or_privileged_prompt_body(
    gateway_setup: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """docs/mvp/04_stack_and_infra.md §2.13: Never log bodies of confidential/privileged payloads."""
    fake_anthropic: FakeModelAdapter = gateway_setup["fake_anthropic"]
    fake_openai: FakeModelAdapter = gateway_setup["fake_openai"]
    valid_resp = json.dumps(
        {
            "claimant": "Secret Client Corp",
            "respondent": "Rival Firm",
            "amount_claimed": 100000.0,
        }
    )
    for adapter in (fake_anthropic, fake_openai):
        adapter.queue_response(valid_resp)

    ctx = ExecutionContext(
        tenant_id=mint_id("ten"),
        user_id=mint_id("usr"),
        firm_role="PARTNER",
        dataclass="PRIVILEGED",
    )

    sensitive_content = "TOP_SECRET_ATTORNEY_CLIENT_WORK_PRODUCT_XYZ123"

    with caplog.at_level(logging.INFO):
        run(
            task_id="extract_notice_parties",
            inputs={"notice_text": sensitive_content},
            ctx=ctx,
        )

    for record in caplog.records:
        # Assert the sensitive content never leaked into logger
        assert sensitive_content not in record.message
        assert sensitive_content not in str(record.__dict__)


@pytest.mark.skipif(
    os.environ.get("RUN_REAL_LLM_TESTS") != "1",
    reason="Real API tests only run when explicitly marked with RUN_REAL_LLM_TESTS=1",
)
def test_real_llm_smoke() -> None:
    """Smoke test against live provider API, skipped during normal CI/dev."""
    pass
