"""Tests for Model Gateway embedding functionality and adapter.

Normative sources:
- Session S06 Directive #7: Embeddings through the Model Gateway with model pinning.
- Directive #7: embed_query from tenant context must send TENANT_CONFIDENTIAL.
- Step 1.2: Assert against real seeded ep_voyage_4_large endpoint.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest

from gateway.adapters.fake import FakeModelAdapter
from gateway.exceptions import NoQualifiedEndpointError
from gateway.models import LLMCallRecord, ModelEndpoint
from gateway.runner import embed, set_adapter_override
from workspace.authz import ExecutionContext


@pytest.fixture(autouse=True)
def fake_adapter() -> Generator[FakeModelAdapter]:
    fake = FakeModelAdapter()
    set_adapter_override("voyage", fake)
    yield fake
    set_adapter_override("voyage", None)


@pytest.mark.django_db
def test_gateway_embed_deterministic(fake_adapter: FakeModelAdapter) -> None:
    # Assert seeded endpoint exists
    endpoint = ModelEndpoint.objects.get(endpoint_id="ep_voyage_4_large")
    assert endpoint.model_id == "voyage-4-large"
    assert endpoint.processing_geo == "US"

    res1 = embed(["Section 138 of Negotiable Instruments Act"], ctx=None)
    assert len(res1.embeddings) == 1
    assert len(res1.embeddings[0]) == 1024

    # Assert normalized unit vector
    norm = sum(x * x for x in res1.embeddings[0]) ** 0.5
    assert pytest.approx(norm, rel=1e-4) == 1.0

    # Deterministic: same text yields same vector
    res2 = embed(["Section 138 of Negotiable Instruments Act"], ctx=None)
    assert res1.embeddings[0] == res2.embeddings[0]

    # Verify LLMCallRecord written with real seeded endpoint
    record = LLMCallRecord.objects.get(call_id=res1.call_record.call_id)
    assert record.task_id == "p2.embed.v1"
    assert record.endpoint_id == "ep_voyage_4_large"
    assert record.dataclass == "PUBLIC"
    assert record.schema_valid is True


@pytest.mark.django_db
def test_gateway_embed_tenant_residency_enforcement() -> None:
    # Seeded endpoint ep_voyage_4_large has processing_geo="US"
    ctx = ExecutionContext(
        tenant_id="ten_01H00000000000000000000000",
        user_id="usr_01H00000000000000000000000",
        firm_role="PARTNER",
        dataclass="PUBLIC",
        residency_policy="IN_ONLY",
    )

    # Fails closed because only US endpoint exists for voyage-4-large
    with pytest.raises(NoQualifiedEndpointError):
        embed(["Confidential matter query"], ctx)


@pytest.mark.django_db
def test_private_chunk_embeddings_never_route_to_us_voyage_endpoint() -> None:
    """Item 4: Confirm private_chunk embeddings can never route to ep_voyage_4_large (US).

    1. Seeded ep_voyage_4_large has processing_geo = 'US'.
    2. Private chunks belong to tpl.private_chunk (tenant plane), where execution context
       enforces residency_policy = 'IN_ONLY' (fail-closed, Non-negotiable #5 / 04 §2.11).
    3. Model Gateway runner verifies residency fail-closed: since ep.processing_geo != 'IN',
       no qualified endpoint is found and NoQualifiedEndpointError is raised.
    """
    endpoint = ModelEndpoint.objects.get(endpoint_id="ep_voyage_4_large")
    assert endpoint.processing_geo == "US"
    assert endpoint.model_id == "voyage-4-large"

    private_chunk_text = "Privileged strategy memo discussing settlement offer of Rs 10 Crore."

    # Standard tenant context for private_chunk indexing (default IN_ONLY residency)
    ctx_tenant = ExecutionContext(
        tenant_id="ten_01H00000000000000000000000",
        user_id="usr_01H00000000000000000000000",
        firm_role="ASSOCIATE",
        dataclass="PUBLIC",
        residency_policy="IN_ONLY",
    )

    with pytest.raises(NoQualifiedEndpointError, match="No qualified endpoint"):
        embed([private_chunk_text], ctx=ctx_tenant)
