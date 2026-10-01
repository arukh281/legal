"""Fake provider adapter for fast, deterministic unit and integration tests."""

from __future__ import annotations

from collections import deque
from typing import Any

from gateway.adapters.base import BaseModelAdapter, LLMResponse
from gateway.models import ModelEndpoint


class FakeModelAdapter(BaseModelAdapter):
    """Deterministic in-memory adapter for testing without calling external APIs."""

    def __init__(self, default_response: str | None = None) -> None:
        self.default_response = default_response or '{"status": "ok"}'
        self.response_queue: deque[LLMResponse | str] = deque()
        self.calls: list[dict[str, Any]] = []

    def queue_response(
        self,
        content: str,
        tokens_in: int = 100,
        tokens_out: int = 50,
        cache_read_tokens: int = 0,
    ) -> None:
        """Enqueue a canned response to be returned by subsequent generate() calls."""
        self.response_queue.append(
            LLMResponse(
                content=content,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cache_read_tokens=cache_read_tokens,
            )
        )

    def generate(
        self,
        endpoint: ModelEndpoint,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        json_mode: bool = True,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        self.calls.append(
            {
                "endpoint_id": endpoint.endpoint_id,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "system_prompt": system_prompt,
            }
        )

        if self.response_queue:
            item = self.response_queue.popleft()
            if isinstance(item, LLMResponse):
                return item
            return LLMResponse(content=item, tokens_in=80, tokens_out=40)

        return LLMResponse(
            content=self.default_response,
            tokens_in=100,
            tokens_out=50,
            cache_read_tokens=0,
        )
