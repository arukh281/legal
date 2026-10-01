"""Base adapter interface and response types for Model Gateway."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from gateway.models import ModelEndpoint


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Standardized response from an LLM adapter call."""

    content: str
    tokens_in: int
    tokens_out: int
    cache_read_tokens: int = 0


class BaseModelAdapter(ABC):
    """Abstract base class for provider adapters."""

    @abstractmethod
    def generate(
        self,
        endpoint: ModelEndpoint,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        json_mode: bool = True,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Execute a text generation call against the model provider."""
