"""Model Gateway execution runner and routing engine.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.15
- docs/mvp/04_stack_and_infra.md §2.8, §2.13
- docs/13_cross_cutting.md §4.3 (Routing algorithm), §4.8
- docs/01a_spine_decision_record.md: D9, D14, D15 (Residency fail-closed)
- Session S03 Directives #1 (unprefixed call_id), #8 (endpoint data_class_max >= call dataclass)
"""

from __future__ import annotations

import decimal
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import jsonschema
from django.utils import timezone

from anchor_lib.ids import mint_ulid
from gateway.adapters.anthropic_adapter import AnthropicAdapter
from gateway.adapters.base import BaseModelAdapter, LLMResponse
from gateway.adapters.fake import FakeModelAdapter
from gateway.adapters.google_adapter import GoogleAdapter
from gateway.adapters.openai_adapter import OpenAIAdapter
from gateway.adapters.voyage_adapter import VoyageAdapter
from gateway.exceptions import (
    BudgetExhaustedError,
    ContractNotFoundError,
    NoQualifiedEndpointError,
    RateLimitError,
    ResidencyFailClosedError,
    SchemaValidationError,
)
from gateway.models import LLMCallRecord, ModelEndpoint, ModelTaskContract
from workspace.authz import ExecutionContext

logger = logging.getLogger(__name__)

DATACLASS_HIERARCHY: dict[str, int] = {
    "PUBLIC": 0,
    "TENANT_CONFIDENTIAL": 1,
    "PRIVILEGED": 2,
}


@dataclass(frozen=True, slots=True)
class GatewayResult:
    """Result returned by a successful gateway execution."""

    output: dict[str, Any]
    call_record: LLMCallRecord
    attempts: int


@dataclass(frozen=True, slots=True)
class GatewayEmbeddingResult:
    """Result returned by a successful gateway embedding execution."""

    embeddings: list[list[float]]
    call_record: LLMCallRecord
    tokens_in: int


# Default provider adapter registry
DEFAULT_ADAPTERS: dict[str, BaseModelAdapter] = {
    "anthropic": AnthropicAdapter(),
    "openai": OpenAIAdapter(),
    "google": GoogleAdapter(),
    "voyage": VoyageAdapter(),
    "fake": FakeModelAdapter(),
}

# Override registry for testing
_ADAPTER_OVERRIDES: dict[str, BaseModelAdapter] = {}


def set_adapter_override(provider: str, adapter: BaseModelAdapter | None) -> None:
    """Override provider adapter with a mock/fake during testing."""
    if adapter is None:
        _ADAPTER_OVERRIDES.pop(provider, None)
    else:
        _ADAPTER_OVERRIDES[provider] = adapter


def _get_adapter(provider: str) -> BaseModelAdapter:
    if provider in _ADAPTER_OVERRIDES:
        return _ADAPTER_OVERRIDES[provider]
    if provider in DEFAULT_ADAPTERS:
        return DEFAULT_ADAPTERS[provider]
    raise NoQualifiedEndpointError(f"No adapter registered for provider '{provider}'.")


def run(
    task_id: str,
    inputs: dict[str, Any],
    ctx: ExecutionContext,
    pipeline_version: str = "v1.0.0",
) -> GatewayResult:
    """Execute a model task through the audited, budgeted, residency-checked Model Gateway.

    Steps:
    1. Load ModelTaskContract by task_id.
    2. Validate inputs against input_schema and max_input_chars.
    3. Filter qualified endpoints (health, qualification, data_class_max, residency fail-closed).
    4. Enforce task budget.
    5. Call adapter and validate output against output_schema.
    6. Allow 1 repair attempt if validation fails; fail loudly if repair fails.
    7. Record LLMCallRecord for every attempt (IDs, hashes, metrics; never privileged bodies).
    """
    # 1. Load contract
    try:
        contract = ModelTaskContract.objects.get(task_id=task_id)
    except ModelTaskContract.DoesNotExist as exc:
        raise ContractNotFoundError(f"ModelTaskContract '{task_id}' not found.") from exc

    # 2. Validate inputs
    serialized_inputs = json.dumps(inputs, sort_keys=True)
    if len(serialized_inputs) > contract.max_input_chars:
        raise SchemaValidationError(
            f"Input character count ({len(serialized_inputs)}) exceeds contract max ({contract.max_input_chars})."
        )
    try:
        jsonschema.validate(instance=inputs, schema=contract.input_schema)
    except jsonschema.ValidationError as exc:
        raise SchemaValidationError(
            f"Inputs failed input_schema validation: {exc.message}"
        ) from exc

    # Check that contract permits the request dataclass
    req_dataclass_level = DATACLASS_HIERARCHY.get(ctx.dataclass, 1)
    contract_max_level = DATACLASS_HIERARCHY.get(contract.data_class_max, 1)
    if req_dataclass_level > contract_max_level:
        raise SchemaValidationError(
            f"Request dataclass '{ctx.dataclass}' exceeds task contract data_class_max '{contract.data_class_max}'."
        )

    # 3. Filter qualified endpoints
    endpoints = list(ModelEndpoint.objects.filter(health__in=["UP", "DEGRADED"]))

    qualified: list[ModelEndpoint] = []
    for ep in endpoints:
        # Check task qualification
        if task_id not in ep.qualified_tasks:
            continue
        # Directive #8: endpoint.data_class_max >= call dataclass
        ep_dataclass_level = DATACLASS_HIERARCHY.get(ep.data_class_max, 0)
        if ep_dataclass_level < req_dataclass_level:
            continue
        qualified.append(ep)

    # Residency enforcement (D15: fail-closed)
    if ctx.residency_policy == "IN_ONLY":
        qualified = [ep for ep in qualified if ep.processing_geo == "IN"]
        if not qualified:
            raise ResidencyFailClosedError(
                "RESIDENCY_NO_QUALIFIED_ENDPOINT: No in-India endpoints available for IN_ONLY policy."
            )

    if not qualified:
        raise NoQualifiedEndpointError(f"No qualified endpoints found for task '{task_id}'.")

    # 4. Enforce budget if specified in context
    max_budget_usd = ctx.llm_policy.get("max_cost_usd")
    spent_usd = ctx.llm_policy.get("spent_usd", 0.0)
    if max_budget_usd is not None and spent_usd >= max_budget_usd:
        raise BudgetExhaustedError(
            f"Task budget exhausted: spent ${spent_usd:.4f} >= limit ${max_budget_usd:.4f}."
        )

    # Order endpoints: IN first for IN_PREFERRED, then batch-capable, then priority, then cheapest
    def sort_key(ep: ModelEndpoint) -> tuple[int, int, int, float]:
        in_prio = 0 if (ctx.residency_policy != "IN_PREFERRED" or ep.processing_geo == "IN") else 1
        batch_prio = 0 if ep.limits.get("supports_batch") else 1
        prio = ep.limits.get("priority", 100) if isinstance(ep.limits, dict) else 100
        in_price = ep.price.get("in_per_mtok", 1.0) if isinstance(ep.price, dict) else 1.0
        return (in_prio, batch_prio, prio, in_price)

    qualified.sort(key=sort_key)

    last_rate_limit_exc: Exception | None = None
    for endpoint in qualified:
        adapter = _get_adapter(endpoint.provider)

        # Render prompt from template
        template = contract.prompt_variants.get(endpoint.provider) or contract.prompt_variants.get(
            "default", "{inputs}"
        )
        prompt = template.format(inputs=serialized_inputs)

        # Prepare call identifiers
        trace_id = ctx.traceparent or mint_ulid()
        now = timezone.now()
        year_str = now.strftime("%Y")
        month_str = now.strftime("%m")
        tenant_part = ctx.tenant_id if ctx.tenant_id else "plc"

        # Attempt 1
        t0 = time.perf_counter()
        try:
            response = adapter.generate(
                endpoint=endpoint,
                prompt=prompt,
                temperature=contract.determinism.get("temperature", 0.0),
                max_tokens=contract.max_output_tokens,
                json_mode=True,
                response_schema=contract.output_schema,
            )
        except RateLimitError as exc:
            logger.warning(
                "Endpoint %s rate limited (429): %s. Failing over to next qualified endpoint.",
                endpoint.endpoint_id,
                exc,
            )
            last_rate_limit_exc = exc
            continue

        latency_ms = int((time.perf_counter() - t0) * 1000)

        # Calculate USD cost
        cost_usd = calculate_cost(endpoint, response)

        # Validate output schema
        parsed_json, schema_valid, val_error = validate_json(response.content, contract.output_schema)

        call_id_1 = mint_ulid()  # Unprefixed ULID per Directive #1
        inputs_ref_1 = f"s3://storage/llm/{tenant_part}/{year_str}/{month_str}/{call_id_1}.in.json.gz"
        outputs_ref_1 = f"s3://storage/llm/{tenant_part}/{year_str}/{month_str}/{call_id_1}.out.json.gz"

        # Write call record for attempt 1
        record_1 = LLMCallRecord.objects.create(
            call_id=call_id_1,
            trace_id=trace_id,
            task_id=task_id,
            endpoint_id=endpoint.endpoint_id,
            pipeline_version=pipeline_version,
            tenant_id=ctx.tenant_id,
            matter_id=ctx.matter_id,
            dataclass=ctx.dataclass,
            residency=ctx.residency_policy,
            processing_geo=endpoint.processing_geo,
            purpose=ctx.purpose,
            input_chars=len(prompt),
            output_chars=len(response.content),
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cache_read_tokens=response.cache_read_tokens,
            usd=cost_usd,
            latency_ms=latency_ms,
            schema_valid=schema_valid,
            repaired=False,
            escalated_from=None,
            inputs_ref=inputs_ref_1,
            outputs_ref=outputs_ref_1,
            created_at=now,
        )

        log_gateway_call(record_1, ctx.dataclass)

        if schema_valid and parsed_json is not None:
            return GatewayResult(output=parsed_json, call_record=record_1, attempts=1)

        # 6. Output invalid -> attempt ONE repair
        repair_prompt = (
            f"Your previous response did not satisfy the required JSON schema:\n"
            f"Validation error: {val_error}\n"
            f"Previous response:\n{response.content}\n"
            f"Please repair and return strictly conforming JSON for schema:\n"
            f"{json.dumps(contract.output_schema)}"
        )

        t0 = time.perf_counter()
        try:
            repair_response = adapter.generate(
                endpoint=endpoint,
                prompt=repair_prompt,
                temperature=0.0,
                max_tokens=contract.max_output_tokens,
                json_mode=True,
                response_schema=contract.output_schema,
            )
        except RateLimitError as exc:
            logger.warning(
                "Endpoint %s rate limited during repair (429): %s. Failing over to next qualified endpoint.",
                endpoint.endpoint_id,
                exc,
            )
            last_rate_limit_exc = exc
            continue

        repair_latency_ms = int((time.perf_counter() - t0) * 1000)
        repair_cost_usd = calculate_cost(endpoint, repair_response)

        repaired_json, repaired_valid, repair_error = validate_json(
            repair_response.content, contract.output_schema
        )

        call_id_2 = mint_ulid()
        inputs_ref_2 = f"s3://storage/llm/{tenant_part}/{year_str}/{month_str}/{call_id_2}.in.json.gz"
        outputs_ref_2 = f"s3://storage/llm/{tenant_part}/{year_str}/{month_str}/{call_id_2}.out.json.gz"

        now_repair = timezone.now()
        record_2 = LLMCallRecord.objects.create(
            call_id=call_id_2,
            trace_id=trace_id,
            task_id=task_id,
            endpoint_id=endpoint.endpoint_id,
            pipeline_version=pipeline_version,
            tenant_id=ctx.tenant_id,
            matter_id=ctx.matter_id,
            dataclass=ctx.dataclass,
            residency=ctx.residency_policy,
            processing_geo=endpoint.processing_geo,
            purpose=ctx.purpose,
            input_chars=len(repair_prompt),
            output_chars=len(repair_response.content),
            tokens_in=repair_response.tokens_in,
            tokens_out=repair_response.tokens_out,
            cache_read_tokens=repair_response.cache_read_tokens,
            usd=repair_cost_usd,
            latency_ms=repair_latency_ms,
            schema_valid=repaired_valid,
            repaired=True,
            escalated_from=call_id_1,
            inputs_ref=inputs_ref_2,
            outputs_ref=outputs_ref_2,
            created_at=now_repair,
        )

        log_gateway_call(record_2, ctx.dataclass)

        if repaired_valid and repaired_json is not None:
            return GatewayResult(output=repaired_json, call_record=record_2, attempts=2)

        raise SchemaValidationError(
            f"Model output schema validation failed after repair: {repair_error}"
        )

    if last_rate_limit_exc is not None:
        raise last_rate_limit_exc
    raise NoQualifiedEndpointError(f"No qualified endpoints succeeded for task '{task_id}'.")


def embed(
    texts: list[str],
    ctx: ExecutionContext | None = None,
    task_id: str = "p2.embed.v1",
    model_id: str = "voyage-4-large",
    dims: int = 1024,
    input_type: str = "document",
    dataclass: str = "PUBLIC",
    pipeline_version: str = "p2.embedder@0.1.0|approx_tok_v1|voyage-4-large|1024",
) -> GatewayEmbeddingResult:
    """Execute vector embedding through the Model Gateway.

    Rules (Session S06 Directive #7):
    - Strict model pinning: endpoint model_id must match requested model_id and dims.
    - No heterogeneous failover: retry with exponential backoff on transient errors, then fail loudly.
    - If called from a tenant context (ctx.tenant_id is not None), dataclass is escalated to
      TENANT_CONFIDENTIAL so residency rules apply.
    - Records an LLMCallRecord with cost, tokens, and hashes (never privileged bodies).
    """
    import hashlib

    if not texts:
        raise ValueError("Cannot embed empty list of texts.")

    # Directive #7: embed_query from tenant context must send TENANT_CONFIDENTIAL
    tenant_id = ctx.tenant_id if ctx else None
    matter_id = ctx.matter_id if ctx else None
    effective_dataclass = "TENANT_CONFIDENTIAL" if tenant_id else dataclass
    req_dataclass_level = DATACLASS_HIERARCHY.get(effective_dataclass, 1)

    # 1. Look up endpoint matching the generation's model_id
    endpoints = list(
        ModelEndpoint.objects.filter(
            health__in=["UP", "DEGRADED"],
            model_id=model_id,
        )
    )

    qualified: list[ModelEndpoint] = []
    for ep in endpoints:
        ep_dataclass_level = DATACLASS_HIERARCHY.get(ep.data_class_max, 0)
        if ep_dataclass_level < req_dataclass_level:
            continue
        # Verify residency fail-closed
        residency_policy = ctx.residency_policy if ctx else "ANY"
        if residency_policy == "IN_ONLY" and ep.processing_geo != "IN":
            continue
        qualified.append(ep)

    if not qualified:
        raise NoQualifiedEndpointError(
            f"No qualified endpoint for model '{model_id}' (dims={dims}) matching dataclass '{effective_dataclass}'."
        )

    endpoint = qualified[0]
    adapter = _get_adapter(endpoint.provider)

    # 2. Retry with backoff (Directive #7: retry with backoff and then fail loudly)
    max_retries = 3
    last_exc: Exception | None = None
    start_time = time.monotonic()
    resp = None

    for attempt in range(max_retries):
        try:
            resp = adapter.embed(
                endpoint=endpoint,
                texts=texts,
                dims=dims,
                input_type=input_type,
            )
            break
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                time.sleep(0.05 * (2**attempt))

    if resp is None:
        raise RuntimeError(
            f"Embedding task failed after {max_retries} attempts: {last_exc}"
        ) from last_exc

    latency_ms = int((time.monotonic() - start_time) * 1000)

    # Calculate cost
    price = endpoint.price or {}
    in_per_mtok = decimal.Decimal(str(price.get("in_per_mtok", 0.12)))
    usd = ((decimal.Decimal(resp.tokens_in) * in_per_mtok) / decimal.Decimal(1_000_000)).quantize(
        decimal.Decimal("0.000001")
    )

    # 3. Write LLMCallRecord
    call_id = mint_ulid()
    if effective_dataclass in ("TENANT_CONFIDENTIAL", "PRIVILEGED"):
        inputs_ref = f"sha256:{hashlib.sha256(json.dumps(texts).encode()).hexdigest()}"
        outputs_ref = f"count:{len(resp.embeddings)}"
    else:
        inputs_ref = f"count:{len(texts)}"
        outputs_ref = f"count:{len(resp.embeddings)}"

    call_record = LLMCallRecord.objects.create(
        call_id=call_id,
        trace_id=f"trc_{call_id}",
        task_id=task_id,
        endpoint_id=endpoint.endpoint_id,
        pipeline_version=pipeline_version,
        tenant_id=tenant_id,
        matter_id=matter_id,
        dataclass=effective_dataclass,
        residency=endpoint.processing_geo,
        processing_geo=endpoint.processing_geo,
        purpose=f"embedding:{input_type}",
        input_chars=sum(len(t) for t in texts),
        output_chars=len(resp.embeddings) * dims * 4,
        tokens_in=resp.tokens_in,
        tokens_out=0,
        cache_read_tokens=0,
        usd=usd,
        latency_ms=latency_ms,
        schema_valid=True,
        repaired=False,
        inputs_ref=inputs_ref,
        outputs_ref=outputs_ref,
    )

    log_gateway_call(call_record, effective_dataclass)

    return GatewayEmbeddingResult(
        embeddings=resp.embeddings,
        call_record=call_record,
        tokens_in=resp.tokens_in,
    )


def validate_json(
    content: str, schema: dict[str, Any]
) -> tuple[dict[str, Any] | None, bool, str | None]:
    """Parse and validate JSON against contract output schema."""
    try:
        parsed = json.loads(content)
        jsonschema.validate(instance=parsed, schema=schema)
        return parsed, True, None
    except json.JSONDecodeError as exc:
        return None, False, f"JSON decode error: {exc}"
    except jsonschema.ValidationError as exc:
        return None, False, f"Schema validation error: {exc.message}"


def calculate_cost(endpoint: ModelEndpoint, response: LLMResponse) -> decimal.Decimal:
    """Calculate USD call cost from endpoint price card."""
    price = endpoint.price
    in_per_mtok = decimal.Decimal(str(price.get("in_per_mtok", 0.0)))
    out_per_mtok = decimal.Decimal(str(price.get("out_per_mtok", 0.0)))
    cache_mult = decimal.Decimal(str(price.get("cache_read_mult", 0.05)))

    in_cost = (decimal.Decimal(response.tokens_in) * in_per_mtok) / decimal.Decimal(1_000_000)
    out_cost = (decimal.Decimal(response.tokens_out) * out_per_mtok) / decimal.Decimal(1_000_000)
    cache_cost = (
        decimal.Decimal(response.cache_read_tokens) * in_per_mtok * cache_mult
    ) / decimal.Decimal(1_000_000)

    total = in_cost + out_cost + cache_cost
    return total.quantize(decimal.Decimal("0.000001"))


def log_gateway_call(record: LLMCallRecord, dataclass: str) -> None:
    """Log model invocation without exposing confidential or privileged prompt bodies (04 §2.13)."""
    # Bodies of TENANT_CONFIDENTIAL and PRIVILEGED payloads are NEVER logged
    logger.info(
        "gateway.call_completed",
        extra={
            "call_id": record.call_id,
            "task_id": record.task_id,
            "endpoint_id": record.endpoint_id,
            "dataclass": dataclass,
            "processing_geo": record.processing_geo,
            "usd": str(record.usd),
            "latency_ms": record.latency_ms,
            "schema_valid": record.schema_valid,
            "repaired": record.repaired,
        },
    )
