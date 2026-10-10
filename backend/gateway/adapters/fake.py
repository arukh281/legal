"""Fake provider adapter for fast, deterministic unit and integration tests."""

from __future__ import annotations

from collections import deque
from typing import Any

from gateway.adapters.base import BaseModelAdapter, EmbeddingResponse, LLMResponse
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
        response_schema: dict[str, Any] | None = None,
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

        if self.default_response == '{"status": "ok"}' and "evidence_chunks" in prompt:
            import json
            import re
            try:
                match = re.search(r'\{.*"evidence_chunks".*\}', prompt, re.DOTALL)
                if match:
                    payload = json.loads(match.group(0))
                    chunks = payload.get("evidence_chunks", [])
                    if chunks:
                        first_chunk = chunks[0]
                        anchor_id = first_chunk.get("anchor_id") or (
                            first_chunk.get("anchor_ids", [""])[0] if first_chunk.get("anchor_ids") else ""
                        )
                        raw_text = first_chunk.get("text") or first_chunk.get("excerpt", "")
                        sentences = [s.strip() for s in raw_text.split(".") if len(s.strip()) > 20]
                        quote = sentences[0] if sentences else raw_text[:80].strip()

                        # Check if paragraph records party submissions
                        is_sub = any(
                            m in raw_text.lower()
                            for m in ["contended", "submitted", "argued", "learned counsel"]
                        )
                        if is_sub:
                            claim_text = f"The appellant contended that {quote}."
                        else:
                            claim_text = f"The statutory record establishes that {quote}."

                        canned = {
                            "summary": f"In {anchor_id}, {claim_text}",
                            "in_corpus": True,
                            "claims": [
                                {
                                    "text": claim_text,
                                    "claim_type": "LEGAL_PROPOSITION",
                                    "anchor_id": anchor_id,
                                    "quote": quote,
                                    "support_type": "DIRECT",
                                }
                            ],
                            "contrary_sweep": {
                                "status": "LIMITED",
                                "notes": "lexical only, no citator",
                            },
                        }
                        return LLMResponse(content=json.dumps(canned), tokens_in=150, tokens_out=80)
            except Exception:
                pass

        return LLMResponse(
            content=self.default_response,
            tokens_in=100,
            tokens_out=50,
            cache_read_tokens=0,
        )

    def embed(
        self,
        endpoint: ModelEndpoint,
        texts: list[str],
        dims: int = 1024,
        input_type: str = "document",
    ) -> EmbeddingResponse:
        """Deterministically generate unit vectors for given texts based on sha256 hash."""
        import hashlib
        import random

        self.calls.append(
            {
                "action": "embed",
                "endpoint_id": endpoint.endpoint_id,
                "texts_count": len(texts),
                "dims": dims,
                "input_type": input_type,
            }
        )

        results: list[list[float]] = []
        total_tokens = 0
        for text in texts:
            # Deterministic pseudo-random seed from sha256
            seed = hashlib.sha256(text.encode("utf-8")).digest()
            rng = random.Random(seed)
            raw = [rng.gauss(0.0, 1.0) for _ in range(dims)]
            norm = sum(x * x for x in raw) ** 0.5
            unit = [x / norm for x in raw] if norm > 0 else [0.0] * dims
            results.append(unit)
            total_tokens += max(1, len(text.split()))

        return EmbeddingResponse(embeddings=results, tokens_in=total_tokens)
