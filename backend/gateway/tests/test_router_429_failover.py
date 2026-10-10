"""Test gateway router 429 failover from ep_gemini_3_8_flash to ep_gemini_3_5_flash.

Normative source: Session S07 Directive #1:
- A 429 on 3.8 produces an LLMCallRecord naming 3.5.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from gateway.adapters.base import BaseModelAdapter, LLMResponse
from gateway.exceptions import RateLimitError
from gateway.models import LLMCallRecord, ModelEndpoint
from gateway.runner import run, set_adapter_override
from workspace.authz import ExecutionContext


class FailoverMockAdapter(BaseModelAdapter):
    """Adapter that raises RateLimitError on 3.8 and succeeds on 3.5."""

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
        if endpoint.endpoint_id == "ep_gemini_3_8_flash":
            raise RateLimitError("Google GenAI model gemini-3.8-flash rate limit (429): RESOURCE_EXHAUSTED")
        if endpoint.endpoint_id == "ep_gemini_3_5_flash":
            return LLMResponse(
                content=json.dumps(
                    {
                        "summary": "Verified answer under Section 14 moratorium.",
                        "in_corpus": True,
                        "claims": [],
                        "contrary_sweep": {"status": "LIMITED", "notes": "lexical only"},
                    }
                ),
                tokens_in=100,
                tokens_out=50,
                cache_read_tokens=0,
            )
        raise RuntimeError(f"Unexpected endpoint called: {endpoint.endpoint_id}")


@pytest.mark.django_db
def test_gateway_429_failover_names_3_5() -> None:
    """A 429 on 3.8 produces an LLMCallRecord naming 3.5."""
    ctx = ExecutionContext(
        tenant_id="tnt_test",
        user_id="usr_test",
        firm_role="ASSOCIATE",
        matter_id=None,
        dataclass="PUBLIC",
        residency_policy="ANY",
        purpose="Q&A Failover Test",
    )

    mock_adapter = FailoverMockAdapter()
    set_adapter_override("google", mock_adapter)

    try:
        inputs = {
            "question": "Does moratorium stay Section 138 proceedings against directors?",
            "as_of_legal_date": "2026-10-10",
            "evidence_chunks": [],
        }

        result = run(
            task_id="p6.qa_synthesis@1",
            inputs=inputs,
            ctx=ctx,
            pipeline_version="p6.reasoner@0.1.0|qa_synthesis_v1",
        )

        # 1. Check endpoints called in order: 3.8 first, then 3.5
        assert mock_adapter.called_endpoints == ["ep_gemini_3_8_flash", "ep_gemini_3_5_flash"]

        # 2. Check that the resulting call record names ep_gemini_3_5_flash
        assert result.call_record.endpoint_id == "ep_gemini_3_5_flash"

        # 3. Verify in database
        saved_record = LLMCallRecord.objects.get(call_id=result.call_record.call_id)
        assert saved_record.endpoint_id == "ep_gemini_3_5_flash"
        assert saved_record.tokens_in == 100
        assert saved_record.tokens_out == 50
        import decimal
        # Cost using 3.5 pricing ($0.075 / $0.30 per Mtok): (100*0.075 + 50*0.30)/1e6 = 0.0000225 -> 0.000022
        assert saved_record.usd == decimal.Decimal("0.000022")
    finally:
        set_adapter_override("google", None)
