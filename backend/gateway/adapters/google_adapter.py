"""Google GenAI SDK adapter for Model Gateway."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, cast

import httpx
from google import genai
from google.genai import errors, types

from gateway.adapters.base import BaseModelAdapter, LLMResponse
from gateway.exceptions import AdapterInvocationError
from gateway.models import ModelEndpoint

logger = logging.getLogger(__name__)


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
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        client = self._get_client()
        primary_model = endpoint.model_snapshot or endpoint.model_id

        # 1. Output token budget & thinking configuration
        # Raise max_output_tokens to at least 8192 so thinking tokens cannot starve the JSON payload
        effective_max_tokens = max(max_tokens, 8192)

        config_args: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": effective_max_tokens,
            # 60s explicit request timeout (HttpOptions expects milliseconds)
            "http_options": types.HttpOptions(timeout=60000),
            # Small thinking budget
            "thinking_config": types.ThinkingConfig(thinking_budget=512),
            "automatic_function_calling": types.AutomaticFunctionCallingConfig(disable=True),
        }
        if system_prompt:
            config_args["system_instruction"] = system_prompt
        if json_mode:
            config_args["response_mime_type"] = "application/json"
            if response_schema:
                config_args["response_schema"] = response_schema

        config = types.GenerateContentConfig(**config_args)

        # Fallback chain: if primary model hits 429 quota exhaustion (e.g. gemini-3.8-flash free tier limit),
        # fall back to qualified active counterpart (gemini-3.5-flash)
        models_to_try = [primary_model]
        if primary_model == "gemini-3.8-flash":
            models_to_try.append("gemini-3.5-flash")

        last_exc: Exception | None = None
        for model_name in models_to_try:
            t0 = time.perf_counter()
            try:
                response = cast(Any, client.models.generate_content)(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                latency_s = time.perf_counter() - t0

                content_text = response.text or ""
                usage = getattr(response, "usage_metadata", None)
                tokens_in = getattr(usage, "prompt_token_count", 0) if usage else 0
                tokens_out = getattr(usage, "candidates_token_count", 0) if usage else 0
                thinking_tokens = getattr(usage, "thoughts_token_count", 0) if usage else 0

                candidates = getattr(response, "candidates", None)
                cand = candidates[0] if candidates else None
                raw_finish = getattr(cand, "finish_reason", "UNKNOWN")
                finish_reason = getattr(raw_finish, "name", str(raw_finish))

                # Item 3: Log per call: latency, finish_reason, thinking tokens, output tokens (no prompt bodies)
                logger.info(
                    "Google GenAI call succeeded: endpoint=%s model=%s latency=%.2fs finish_reason=%s thinking_tokens=%s tokens_out=%s",
                    endpoint.endpoint_id,
                    model_name,
                    latency_s,
                    finish_reason,
                    thinking_tokens,
                    tokens_out,
                )
                print(
                    f"  [GoogleAdapter] Model={model_name} | Latency={latency_s:.2f}s | "
                    f"FinishReason={finish_reason} | ThinkingTokens={thinking_tokens} | OutputTokens={tokens_out}"
                )

                return LLMResponse(
                    content=content_text,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    cache_read_tokens=0,
                )
            except errors.ClientError as exc:
                if "RESOURCE_EXHAUSTED" in str(exc) or getattr(exc, "code", None) == 429:
                    logger.warning(
                        "Google GenAI model %s quota exhausted (429): %s. Checking fallback.",
                        model_name,
                        exc,
                    )
                    last_exc = exc
                    continue
                raise AdapterInvocationError(f"Google GenAI client error: {exc}") from exc
            except (TimeoutError, httpx.TimeoutException) as exc:
                raise AdapterInvocationError(
                    f"Google GenAI API call timed out after 60s: {exc}"
                ) from exc
            except errors.ServerError as exc:
                if getattr(exc, "code", None) == 504 or "DEADLINE_EXCEEDED" in str(exc):
                    raise AdapterInvocationError(
                        f"Google GenAI API call timed out after 60s (504 DEADLINE_EXCEEDED): {exc}"
                    ) from exc
                raise AdapterInvocationError(f"Google GenAI server error: {exc}") from exc
            except Exception as exc:
                if "deadline" in str(exc).lower() or "timeout" in str(exc).lower():
                    raise AdapterInvocationError(
                        f"Google GenAI API call timed out after 60s: {exc}"
                    ) from exc
                raise AdapterInvocationError(f"Google GenAI API call failed: {exc}") from exc

        if last_exc:
            raise AdapterInvocationError(f"Google GenAI API call failed after trying models: {last_exc}") from last_exc
        raise AdapterInvocationError("Google GenAI API call failed: no models attempted.")
