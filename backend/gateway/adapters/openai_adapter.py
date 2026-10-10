"""OpenAI SDK adapter for Model Gateway."""

from __future__ import annotations

import os
from typing import Any, cast

import openai

from gateway.adapters.base import BaseModelAdapter, LLMResponse
from gateway.exceptions import AdapterInvocationError
from gateway.models import ModelEndpoint


class OpenAIAdapter(BaseModelAdapter):
    """Adapter invoking OpenAI models via the official SDK."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._client: openai.OpenAI | None = None

    def _get_client(self) -> openai.OpenAI:
        if self._client is None:
            if not self.api_key:
                raise AdapterInvocationError("OPENAI_API_KEY is not configured.")
            self._client = openai.OpenAI(api_key=self.api_key)
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
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, object] = {
            "model": endpoint.model_snapshot or endpoint.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = cast(Any, client.chat.completions.create)(**kwargs)
            choice = response.choices[0]
            content_text = choice.message.content or ""

            usage = response.usage
            tokens_in = getattr(usage, "prompt_tokens", 0) if usage else 0
            tokens_out = getattr(usage, "completion_tokens", 0) if usage else 0

            return LLMResponse(
                content=content_text,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cache_read_tokens=0,
            )
        except Exception as exc:
            raise AdapterInvocationError(f"OpenAI API call failed: {exc}") from exc
