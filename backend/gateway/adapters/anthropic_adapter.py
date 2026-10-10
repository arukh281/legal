"""Anthropic SDK adapter for Model Gateway."""

from __future__ import annotations

import os
from typing import Any, cast

import anthropic

from gateway.adapters.base import BaseModelAdapter, LLMResponse
from gateway.exceptions import AdapterInvocationError
from gateway.models import ModelEndpoint


class AnthropicAdapter(BaseModelAdapter):
    """Adapter invoking Anthropic models via the official SDK."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client: anthropic.Anthropic | None = None

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            if not self.api_key:
                raise AdapterInvocationError("ANTHROPIC_API_KEY is not configured.")
            self._client = anthropic.Anthropic(api_key=self.api_key)
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
        client = self._get_client()
        messages = [{"role": "user", "content": prompt}]
        kwargs: dict[str, object] = {
            "model": endpoint.model_snapshot or endpoint.model_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = cast(Any, client.messages.create)(**kwargs)
            # Extract content text
            content_blocks = [b.text for b in response.content if hasattr(b, "text")]
            content_text = "".join(content_blocks)

            tokens_in = getattr(response.usage, "input_tokens", 0)
            tokens_out = getattr(response.usage, "output_tokens", 0)
            cache_read_tokens = getattr(response.usage, "cache_read_input_tokens", 0) or 0

            return LLMResponse(
                content=content_text,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cache_read_tokens=cache_read_tokens,
            )
        except Exception as exc:
            raise AdapterInvocationError(f"Anthropic API call failed: {exc}") from exc
