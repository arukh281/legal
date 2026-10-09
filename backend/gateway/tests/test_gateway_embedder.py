"""Tests for Model Gateway embedding functionality and adapter.

Normative sources:
- Session S06 Directive #7: Embeddings through the Model Gateway with model pinning.
- Directive #7: embed_query from tenant context must send TENANT_CONFIDENTIAL.
"""

from __future__ import annotations

import pytest

from gateway.adapters.fake import FakeModelAdapter
from gateway.exceptions import NoQualifiedEndpointError, ResidencyFailClosedError
from gateway.models import LLMCallRecord, ModelEndpoint, ModelTaskContract
from gateway.runner import embed, set_adapter_override
from workspace.authz import ExecutionContext


@pytest.fixture(autouse=True)
def fake_adapter() -> FakeModelAdapter:
    fake = FakeModelAdapter()
    set_adapter_override("voyage", fake)
    yield fake
    set_adapter_override("voyage", None)


@pytest.mark.django_db
def test_gateway_embed_deterministic(fake_adapter: FakeModelAdapter) -> None:
    ModelEndpoint.objects.create(
        endpoint_id="voyage-test",
        provider="voyage",
        model_id="voyage-4-large",
        model_snapshot="2026-01-01",
        processing_geo="IN",
        zdr=True,
        data_class_max="PRIVILEGED",
        price={"in_per_mtok": 0.12, "out_per_mtok": 0.0},
        limits={"dims": 1024},
        health="UP",
        qualified_tasks={"p2.embed.v1": {}},
    )

    res1 = embed(["Section 138 of Negotiable Instruments Act"], ctx=None)
    assert len(res1.embeddings) == 1
    assert len(res1.embeddings[0]) == 1024

    # Assert normalized unit vector
    norm = sum(x * x for x in res1.embeddings[0]) ** 0.5
    assert pytest.approx(norm, rel=1e-4) == 1.0

    # Deterministic: same text yields same vector
    res2 = embed(["Section 138 of Negotiable Instruments Act"], ctx=None)
    assert res1.embeddings[0] == res2.embeddings[0]

    # Verify LLMCallRecord written
    record = LLMCallRecord.objects.get(call_id=res1.call_record.call_id)
    assert record.task_id == "p2.embed.v1"
    assert record.endpoint_id == "voyage-test"
    assert record.dataclass == "PUBLIC"
    assert record.schema_valid is True


@pytest.mark.django_db
def test_gateway_embed_tenant_residency_enforcement() -> None:
    ModelEndpoint.objects.create(
        endpoint_id="voyage-us",
        provider="voyage",
        model_id="voyage-4-large",
        model_snapshot="2026-01-01",
        processing_geo="US",
        zdr=True,
        data_class_max="PRIVILEGED",
        price={"in_per_mtok": 0.12},
        limits={"dims": 1024},
        health="UP",
        qualified_tasks={"p2.embed.v1": {}},
    )

    ctx = ExecutionContext(
        tenant_id="ten_01H00000000000000000000000",
        user_id="usr_01H00000000000000000000000",
        firm_role="PARTNER",
        dataclass="PUBLIC",
        residency_policy="IN_ONLY",
    )

    # Fails closed because only US endpoint exists
    with pytest.raises(NoQualifiedEndpointError):
        embed(["Confidential matter query"], ctx)
