"""anchor_lib: Normative identifier minting, anchor grammar v1.1, and selectors."""

from typing import Any

from anchor_lib.anchors import (
    AnchorRef,
    ExpressionInfo,
    FallbackFragment,
    InvalidAnchorError,
    JudgmentExpression,
    JudgmentFragment,
    NoExpressionError,
    PITRef,
    PrivateAnchor,
    ProvisionRef,
    PublicAnchor,
    SemanticConstraintError,
    StatuteExpression,
    StatuteFragment,
    StatuteSegment,
    canonical_key,
    check_reconstructed_text,
    check_translation_support,
    format,
    get_clause_hierarchy,
    is_fallback_locator,
    is_private,
    is_public,
    parse,
    resolve_pit,
    rewrite_statute_expression,
    validate,
)
from anchor_lib.case_numbers import (
    NormalizedCaseNumber,
    compare_case_numbers,
    normalize_bench,
    normalize_case_number,
)
from anchor_lib.ids import (
    MNEMONIC_PREFIXES,
    PREFIX_REGISTRY,
    ParsedID,
    is_valid_id,
    is_valid_sha256,
    mint_id,
    parse_id,
)
from anchor_lib.selectors import QuoteSelector

__all__ = [
    "AnchorRef",
    "DomainModel",
    "ExpressionInfo",
    "FallbackFragment",
    "IDMinter",
    "InvalidAnchorError",
    "JudgmentExpression",
    "JudgmentFragment",
    "MNEMONIC_PREFIXES",
    "NoExpressionError",
    "NormalizedCaseNumber",
    "PITRef",
    "PREFIX_REGISTRY",
    "ParsedID",
    "PrefixedULIDField",
    "PrivateAnchor",
    "ProvisionRef",
    "PublicAnchor",
    "QuoteSelector",
    "SemanticConstraintError",
    "StatuteExpression",
    "StatuteFragment",
    "StatuteSegment",
    "canonical_key",
    "check_reconstructed_text",
    "check_translation_support",
    "compare_case_numbers",
    "format",
    "get_clause_hierarchy",
    "is_fallback_locator",
    "is_private",
    "is_public",
    "is_valid_id",
    "is_valid_sha256",
    "mint_id",
    "normalize_bench",
    "normalize_case_number",
    "parse",
    "parse_id",
    "resolve_pit",
    "rewrite_statute_expression",
    "validate",
]


def __getattr__(name: str) -> Any:
    if name in ("DomainModel", "PrefixedULIDField", "IDMinter"):
        import anchor_lib.models as models_mod

        return getattr(models_mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
