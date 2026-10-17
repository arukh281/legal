"""Tests for Claude Sonnet 5.5 priority routing, daily budget cap, and verifier family separation.

Normative source:
- Item 4 of S09 preparation session:
  - Repoint ep_claude_sonnet_3_5 to new endpoint for claude-sonnet-5-5 as priority 1 for p6.qa_synthesis; Gemini stays as fallback.
  - Set a daily budget cap in the gateway.
  - Record the verifier/judge family as Gemini so generator != verifier.
"""

from __future__ import annotations

import decimal
import json
from typing import Any

import pytest
from django.conf import settings
from django.utils import timezone

from anchor_lib.ids import mint_ulid
from gateway.adapters.base import BaseModelAdapter, LLMResponse
from gateway.exceptions import BudgetExhaustedError, RateLimitError
from gateway.models import LLMCallRecord, ModelEndpoint
from gateway.runner import run, set_adapter_override
from ops.models import PipelineVersion
from workspace.authz import ExecutionContext


class MockClaudeAdapter(BaseModelAdapter):
    """Mock adapter for Claude tests."""

    def __init__(self, should_fail_429: bool = False) -> None:
        self.should_fail_429 = should_fail_429
        self.called_endpoints: list[str] = []

    def generate(
        self,
        endpoint: ModelEndpoint,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        json_mode: bool = True,
        system_prompt: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        self.called_endpoints.append(endpoint.endpoint_id)
        if self.should_fail_429:
            raise RateLimitError("Anthropic rate limit: 429 Too Many Requests")
        return LLMResponse(
            content=json.dumps(
                {
                    "summary": "Claude Sonnet 5.5 answered.",
                    "in_corpus": True,
                    "claims": [],
                    "contrary_sweep": {"status": "NONE", "notes": "No contrary authority"},
                }
            ),
            tokens_in=120,
            tokens_out=40,
            cache_read_tokens=0,
        )


class MockGeminiAdapter(BaseModelAdapter):
    """Mock adapter for Gemini fallback."""

    def __init__(self) -> None:
        self.called_endpoints: list[str] = []

    def generate(
        self,
        endpoint: ModelEndpoint,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        json_mode: bool = True,
        system_prompt: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        self.called_endpoints.append(endpoint.endpoint_id)
        return LLMResponse(
            content=json.dumps(
                {
                    "summary": "Gemini fallback answered.",
                    "in_corpus": True,
                    "claims": [],
                    "contrary_sweep": {"status": "NONE", "notes": "No contrary authority"},
                }
            ),
            tokens_in=100,
            tokens_out=50,
            cache_read_tokens=0,
        )


@pytest.mark.django_db
def test_claude_sonnet_5_5_is_priority_1_for_qa_synthesis() -> None:
    """Claude Sonnet 5.5 is selected first as priority 1 for p6.qa_synthesis@1."""
    claude_mock = MockClaudeAdapter(should_fail_429=False)
    gemini_mock = MockGeminiAdapter()

    set_adapter_override("anthropic", claude_mock)
    set_adapter_override("google", gemini_mock)

    try:
        ctx = ExecutionContext(
            tenant_id="tnt_test",
            user_id="usr_test",
            firm_role="ASSOCIATE",
            dataclass="PUBLIC",
            residency_policy="ANY",
        )
        inputs = {
            "question": "Can NCLT review CoC commercial wisdom?",
            "as_of_legal_date": "2026-10-10",
            "evidence_chunks": [],
        }

        result = run(task_id="p6.qa_synthesis@1", inputs=inputs, ctx=ctx)

        # ep_claude_sonnet_5_5 must be the first endpoint called
        assert claude_mock.called_endpoints == ["ep_claude_sonnet_5_5"]
        assert result.call_record.endpoint_id == "ep_claude_sonnet_5_5"
        # Gemini should not have been called since Claude succeeded
        assert gemini_mock.called_endpoints == []
    finally:
        set_adapter_override("anthropic", None)
        set_adapter_override("google", None)


@pytest.mark.django_db
def test_claude_429_fails_over_to_gemini_fallback() -> None:
    """When Claude returns 429, gateway falls back to Gemini."""
    claude_mock = MockClaudeAdapter(should_fail_429=True)
    gemini_mock = MockGeminiAdapter()

    set_adapter_override("anthropic", claude_mock)
    set_adapter_override("google", gemini_mock)

    try:
        ctx = ExecutionContext(
            tenant_id="tnt_test",
            user_id="usr_test",
            firm_role="ASSOCIATE",
            dataclass="PUBLIC",
            residency_policy="ANY",
        )
        inputs = {
            "question": "Can NCLT review CoC commercial wisdom?",
            "as_of_legal_date": "2026-10-10",
            "evidence_chunks": [],
        }

        result = run(task_id="p6.qa_synthesis@1", inputs=inputs, ctx=ctx)

        # Claude failed, then Gemini succeeded
        assert claude_mock.called_endpoints == ["ep_claude_sonnet_5_5"]
        assert gemini_mock.called_endpoints == ["ep_gemini_3_8_flash"]
        assert result.call_record.endpoint_id == "ep_gemini_3_8_flash"
    finally:
        set_adapter_override("anthropic", None)
        set_adapter_override("google", None)


@pytest.mark.django_db
def test_gateway_daily_budget_cap_enforcement(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gateway halts calls when today's spend exceeds GATEWAY_DAILY_BUDGET_USD."""
    # Set cap to $10.00
    monkeypatch.setattr(settings, "GATEWAY_DAILY_BUDGET_USD", 10.0)

    # Record existing spend of $12.50 today
    now = timezone.now()
    LLMCallRecord.objects.create(
        call_id=mint_ulid(),
        trace_id="trc_budget_test",
        task_id="p6.qa_synthesis@1",
        endpoint_id="ep_claude_sonnet_5_5",
        pipeline_version="p6.reasoner@0.1.0|qa_synthesis_v1",
        dataclass="PUBLIC",
        residency="ANY",
        processing_geo="US",
        input_chars=1000,
        output_chars=500,
        tokens_in=250,
        tokens_out=100,
        usd=decimal.Decimal("12.500000"),
        latency_ms=800,
        schema_valid=True,
        repaired=False,
        inputs_ref="count:1",
        outputs_ref="count:1",
        created_at=now,
    )

    ctx = ExecutionContext(
        tenant_id="tnt_test",
        user_id="usr_test",
        firm_role="ASSOCIATE",
        dataclass="PUBLIC",
        residency_policy="ANY",
    )
    inputs = {
        "question": "Test budget cap question",
        "as_of_legal_date": "2026-10-10",
        "evidence_chunks": [],
    }

    with pytest.raises(BudgetExhaustedError) as exc_info:
        run(task_id="p6.qa_synthesis@1", inputs=inputs, ctx=ctx)

    assert "Gateway daily budget cap exhausted" in str(exc_info.value)


@pytest.mark.django_db
def test_verifier_family_is_gemini_and_distinct_from_generator() -> None:
    """Verifier pipeline version records model_id='gemini-3.8-flash' ensuring generator != verifier."""
    pv = PipelineVersion.objects.get(pipeline_version="p8.verifier@0.1.0|ladder_c0_c2_v1")
    assert pv.model_id == "gemini-3.8-flash"
    assert pv.model_snapshot == "gemini-3.8-flash"
