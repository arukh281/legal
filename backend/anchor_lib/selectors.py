"""QuoteSelector implementation for durable anchor re-alignment.

Normative sources:
- docs/01_master_architecture.md §5.5 item 7:
  "Durable records store anchors plus quote_selector (prefix and suffix,
   TextQuoteSelector-style), so a tenant memo can be re-anchored even after an ID change."
- docs/01_master_architecture.md §7.1:
  "quote_selector: { prefix: string; suffix: string };"
- docs/mvp/03_data_model_and_contracts.md §1 item 6 & §3.4 line 283:
  "quote_prefix text, quote_suffix text, -- quote_selector"
- docs/03_P1_ingestion_parsing.md line 914:
  "quote_selector = (prefix 32 chars, exact text, suffix 32 chars), in the style of
   W3C Web Annotation TextQuoteSelector"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class QuoteSelector:
    """W3C-style TextQuoteSelector holding exact text and surrounding context.

    Enables re-anchoring of claims, memos, and citations even after document re-parsing
    or ID changes.
    """

    exact: str
    prefix: str = ""
    suffix: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.exact, str):
            raise TypeError("QuoteSelector.exact must be a string")
        if not isinstance(self.prefix, str):
            raise TypeError("QuoteSelector.prefix must be a string")
        if not isinstance(self.suffix, str):
            raise TypeError("QuoteSelector.suffix must be a string")

    @classmethod
    def from_text(
        cls,
        full_text: str,
        start: int,
        end: int,
        max_context: int = 32,
    ) -> QuoteSelector:
        """Create a QuoteSelector from full text and character offsets."""
        if start < 0 or end > len(full_text) or start > end:
            raise ValueError(f"Invalid offsets [{start}:{end}] for text length {len(full_text)}")
        exact = full_text[start:end]
        prefix_start = max(0, start - max_context)
        prefix = full_text[prefix_start:start]
        suffix_end = min(len(full_text), end + max_context)
        suffix = full_text[end:suffix_end]
        return cls(exact=exact, prefix=prefix, suffix=suffix)

    def find_in(self, target_text: str) -> tuple[int, int] | None:
        """Locate exact text within target_text using prefix and suffix to disambiguate.

        Returns (start, end) character offsets in target_text, or None if not found.
        """
        if not self.exact:
            return None

        # Find all occurrences of exact text
        candidates: list[int] = []
        idx = target_text.find(self.exact)
        while idx != -1:
            candidates.append(idx)
            idx = target_text.find(self.exact, idx + 1)

        if not candidates:
            return None

        if len(candidates) == 1:
            start = candidates[0]
            return start, start + len(self.exact)

        # Multiple occurrences: rank by prefix and suffix match score
        best_candidate: int | None = None
        best_score = -1

        for c in candidates:
            score = 0
            # Check prefix matching backwards from c
            if self.prefix:
                pre_window = target_text[max(0, c - len(self.prefix)) : c]
                # count common suffix between self.prefix and pre_window
                common_pre = 0
                for a, b in zip(reversed(self.prefix), reversed(pre_window), strict=False):
                    if a == b:
                        common_pre += 1
                    else:
                        break
                score += common_pre

            # Check suffix matching forwards from end
            end = c + len(self.exact)
            if self.suffix:
                post_window = target_text[end : end + len(self.suffix)]
                common_post = 0
                for a, b in zip(self.suffix, post_window, strict=False):
                    if a == b:
                        common_post += 1
                    else:
                        break
                score += common_post

            if score > best_score:
                best_score = score
                best_candidate = c

        if best_candidate is not None:
            return best_candidate, best_candidate + len(self.exact)

        return None

    def to_dict(self) -> dict[str, str]:
        return {
            "exact": self.exact,
            "prefix": self.prefix,
            "suffix": self.suffix,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QuoteSelector:
        return cls(
            exact=str(data.get("exact", "")),
            prefix=str(data.get("prefix", "")),
            suffix=str(data.get("suffix", "")),
        )
