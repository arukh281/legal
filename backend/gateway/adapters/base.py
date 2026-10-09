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


@dataclass(frozen=True, slots=True)
class EmbeddingResponse:
    """Standardized response from an embedding adapter call."""

    embeddings: list[list[float]]
    tokens_in: int


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

    def embed(
        self,
        endpoint: ModelEndpoint,
        texts: list[str],
        dims: int = 1024,
        input_type: str = "document",
    ) -> EmbeddingResponse:
        """Execute an embedding call against the model provider."""
        raise NotImplementedError(
            f"Embedding is not supported by adapter {self.__class__.__name__}"
        )

