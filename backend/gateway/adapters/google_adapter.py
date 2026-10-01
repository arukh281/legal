"""Google GenAI SDK adapter for Model Gateway."""

from __future__ import annotations

import os
from typing import Any, cast

from google import genai

from gateway.adapters.base import BaseModelAdapter, LLMResponse
from gateway.exceptions import AdapterInvocationError
from gateway.models import ModelEndpoint


class GoogleAdapter(BaseModelAdapter):
    """Adapter invoking Google Gemini models via the official GenAI SDK."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = (
            api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        )
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if not self.api_key:
                raise AdapterInvocationError("GEMINI_API_KEY/GOOGLE_API_KEY is not configured.")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate(
        self,
        endpoint: ModelEndpoint,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        json_mode: bool = True,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        client = self._get_client()
        model_name = endpoint.model_snapshot or endpoint.model_id

        config: dict[str, object] = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_prompt:
            config["system_instruction"] = system_prompt
        if json_mode:
            config["response_mime_type"] = "application/json"

        try:
            response = cast(Any, client.models.generate_content)(
                model=model_name,
                contents=prompt,
                config=config,
            )
            content_text = response.text or ""
            usage = getattr(response, "usage_metadata", None)
            tokens_in = getattr(usage, "prompt_token_count", 0) if usage else 0
            tokens_out = getattr(usage, "candidates_token_count", 0) if usage else 0

            return LLMResponse(
                content=content_text,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cache_read_tokens=0,
            )
        except Exception as exc:
            raise AdapterInvocationError(f"Google GenAI API call failed: {exc}") from exc
