"""Voyage AI provider adapter for vector embeddings.

Normative sources:
- docs/mvp/04_stack_and_infra.md §2.5 (voyage-4-large default)
- Session S06 Directive #2: Official voyageai SDK inside gateway/adapters/
"""

from __future__ import annotations

import os
from typing import Any

import voyageai

from gateway.adapters.base import BaseModelAdapter, EmbeddingResponse, LLMResponse
from gateway.models import ModelEndpoint


class VoyageAdapter(BaseModelAdapter):
    """Adapter for Voyage AI embedding models."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("VOYAGE_API_KEY", "")
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            client_cls = voyageai.Client  # type: ignore[attr-defined]
            self._client = client_cls(api_key=self.api_key)
        return self._client

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
        raise NotImplementedError("Voyage AI adapter does not support text generation.")

    def embed(
        self,
        endpoint: ModelEndpoint,
        texts: list[str],
        dims: int = 1024,
        input_type: str = "document",
    ) -> EmbeddingResponse:
        """Call Voyage API client.embed()."""
        client = self._get_client()
        res = client.embed(
            texts=texts,
            model=endpoint.model_id,
            input_type=input_type,
            output_dimension=dims,
        )
        return EmbeddingResponse(
            embeddings=res.embeddings,
            tokens_in=getattr(res, "total_tokens", 0),
        )
