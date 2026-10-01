"""Tests for Anchor Grammar v1.1, parsing, formatting, canonicalization, and A1–A8.

Normative sources:
- docs/01_master_architecture.md §5.3 (formal EBNF grammar v1.0, examples, constraints A1-A8)
- docs/01a_spine_decision_record.md (D8, D16, D21.8, D21.17, D22.2)
- docs/mvp/03_data_model_and_contracts.md §1 item 3
"""

from __future__ import annotations

import pytest

from anchor_lib.anchors import (
    ExpressionInfo,
    InvalidAnchorError,
    NoExpressionError,
    PrivateAnchor,
    SemanticConstraintError,
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

# Every normative example from 01 §5.3 and D22.2
NORMATIVE_EXAMPLES = [
    # Judgment paragraphs
    "wrk_01J9Z0123456789ABCDEFGHJKM/en#p45",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en#o2.p14",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en#p45.s3",
    "wrk_01J9Z0123456789ABCDEFGHJKM/hi#ord",
    "wrk_01J9Z0123456789ABCDEFGHJKM/hi#hdr",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en#fn3",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en#u7",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en#p45.2",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en#p12.a",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en#p12.u1",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en#p45.x1",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en.r2#p45",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en#o1.p45",
    # Statute fragments & point-in-time
    "wrk_01J9Z0123456789ABCDEFGHJKM/en@2003-02-06#sec-138.p1",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en@2003-02-06#sec-138.p1.c",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en@2024-07-01#art-19.1.a",
    "wrk_01J9Z0123456789ABCDEFGHJKM#sec-302",
    "wrk_01J9Z0123456789ABCDEFGHJKM#sec-302@2023-12-31",
    "wrk_01J9Z0123456789ABCDEFGHJKM#sec-3@2019-08-09~IN-UP",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en@2003-02-06#sec-302.e1",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en@2003-02-06#sec-302.ill-a",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en@2003-02-06#sec-302.ill-1",
    # Schedule grammar v1.1 D22.2
    "wrk_01J9Z0123456789ABCDEFGHJKM/en@2024-07-01#sch-1.ord-8.rule-1",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en@2024-07-01#sch-1.ord-39.rule-2A",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en@2024-07-01#sch-1.item-5",
    # Fallback locator
    "wrk_01J9Z0123456789ABCDEFGHJKM/en#pg7.l14",
    "wrk_01J9Z0123456789ABCDEFGHJKM/en#pg7",
    # Private anchors (D8)
    "pdoc_01J9Z0123456789ABCDEFGHJKM/v2#p12",
    "pdoc_01J9Z0123456789ABCDEFGHJKM/v1#hdr.subject",
    "pdoc_01J9Z0123456789ABCDEFGHJKM/v1#hdr.from",
    "pdoc_01J9Z0123456789ABCDEFGHJKM/v1#att2/p4",
    "pdoc_01J9Z0123456789ABCDEFGHJKM/v1#sheet2.r15.c4",
    "pdoc_01J9Z0123456789ABCDEFGHJKM/v1#r15.c4",
    "pdoc_01J9Z0123456789ABCDEFGHJKM/v1#t00:03:15-00:03:40",
    "pdoc_01J9Z0123456789ABCDEFGHJKM/v1.mt-en#p12",
    "pdoc_01J9Z0123456789ABCDEFGHJKM/v1.ht-en#p12",
    "pdoc_01J9Z0123456789ABCDEFGHJKM/v1#pg3.rg2",
    "pdoc_01J9Z0123456789ABCDEFGHJKM/v1#m12",
    "pdoc_01J9Z0123456789ABCDEFGHJKM/v1#m12.att2",
]


@pytest.mark.parametrize("example", NORMATIVE_EXAMPLES)
def test_all_normative_examples_parse_and_roundtrip(example: str) -> None:
    """Ensure every example in 01 §5.3 and D22 parses, and format(parse(x)) == x exactly."""
    parsed = parse(example)
    assert parsed is not None
    # User instruction 4: format() must reproduce the input exactly
    formatted = format(parsed)
    assert formatted == example, f"Roundtrip failed for {example}: got {formatted}"


def test_public_and_private_classification() -> None:
    """Check is_public and is_private properties across anchor kinds."""
    pub = parse("wrk_01J9Z0123456789ABCDEFGHJKM/en#p45")
    assert is_public(pub) is True
    assert is_private(pub) is False
    assert pub.is_public is True
    assert pub.is_private is False

    prov = parse("wrk_01J9Z0123456789ABCDEFGHJKM#sec-302")
    assert is_public(prov) is True
    assert is_private(prov) is False

    pit = parse("wrk_01J9Z0123456789ABCDEFGHJKM#sec-302@2023-12-31")
    assert is_public(pit) is True
    assert is_private(pit) is False

    priv = parse("pdoc_01J9Z0123456789ABCDEFGHJKM/v1#p12")
    assert is_public(priv) is False
    assert is_private(priv) is True
    assert priv.is_public is False
    assert priv.is_private is True


def test_constraint_a1_paragraph_source_failing_examples() -> None:
    """A1 Paragraph source: p0 and u0 are invalid; posint >= 1."""
    with pytest.raises(InvalidAnchorError, match="Paragraph number cannot be zero|posint"):
        parse("wrk_01J9Z0123456789ABCDEFGHJKM/en#p0")

    with pytest.raises(InvalidAnchorError, match="Paragraph number cannot be zero|posint"):
        parse("wrk_01J9Z0123456789ABCDEFGHJKM/en#u0")

    with pytest.raises(InvalidAnchorError):
        parse("wrk_01J9Z0123456789ABCDEFGHJKM/en#p-1")


def test_constraint_a2_fallback_locator_failing_example() -> None:
    """A2 Fallback locators: pg/pg.l fragments exist only for QUARANTINED documents."""
    anchor = "wrk_01J9Z0123456789ABCDEFGHJKM/en#pg7.l14"
    assert is_fallback_locator(anchor) is True

    # Valid if quarantined
    validate(anchor, is_quarantined=True)

    # Failing example: doc not quarantined raises SemanticConstraintError
    with pytest.raises(SemanticConstraintError, match="Constraint A2 violation"):
        validate(anchor, is_quarantined=False)


def test_constraint_a3_pit_resolution_and_failing_example() -> None:
    """A3 Point-in-time resolution: resolves by date and territory precedence; NO_EXPRESSION on gap."""
    pit_ref = "wrk_01J9Z0123456789ABCDEFGHJKM#sec-302@2023-05-15"
    expressions = [
        ExpressionInfo(
            expression_key="en@2000-01-01",
            lang="en",
            valid_from="2000-01-01",
            valid_to="2020-01-01",
        ),
        ExpressionInfo(
            expression_key="en@2020-01-01",
            lang="en",
            valid_from="2020-01-01",
            valid_to="2024-01-01",
        ),
    ]

    resolved = resolve_pit(pit_ref, expressions)
    assert format(resolved) == "wrk_01J9Z0123456789ABCDEFGHJKM/en@2020-01-01#sec-302"

    # Territory precedence test: territorial expression ~IN-UP takes precedence over national
    pit_state = "wrk_01J9Z0123456789ABCDEFGHJKM#sec-3@2021-06-01~IN-UP"
    exprs_with_terr = [
        ExpressionInfo(
            expression_key="en@2020-01-01",
            lang="en",
            valid_from="2020-01-01",
            valid_to=None,
            territory=None,
        ),
        ExpressionInfo(
            expression_key="en@2020-01-01~IN-UP",
            lang="en",
            valid_from="2020-01-01",
            valid_to=None,
            territory="IN-UP",
        ),
    ]
    resolved_terr = resolve_pit(pit_state, exprs_with_terr)
    assert format(resolved_terr) == "wrk_01J9Z0123456789ABCDEFGHJKM/en@2020-01-01~IN-UP#sec-3"

    # Failing example: date outside coverage raises NoExpressionError, never nearest
    pit_gap = "wrk_01J9Z0123456789ABCDEFGHJKM#sec-302@1995-01-01"
    with pytest.raises(NoExpressionError, match="NO_EXPRESSION"):
        resolve_pit(pit_gap, expressions)


def test_constraint_a4_reconstructed_text_failing_example() -> None:
    """A4 Reconstructed text: derived=True backs tier-1 claims only if verification=ROUNDTRIP_OK."""
    anchor = "wrk_01J9Z0123456789ABCDEFGHJKM/en@2024-07-01#sec-302"

    # Non-tier 1 is OK even if UNVERIFIED
    assert (
        check_reconstructed_text(anchor, derived=True, verification="UNVERIFIED", impact_tier=2)
        is True
    )

    # Tier 1 with ROUNDTRIP_OK is OK
    assert (
        check_reconstructed_text(anchor, derived=True, verification="ROUNDTRIP_OK", impact_tier=1)
        is True
    )

    # Failing example: tier 1 with UNVERIFIED returns False
    assert (
        check_reconstructed_text(anchor, derived=True, verification="UNVERIFIED", impact_tier=1)
        is False
    )


def test_constraint_a5_translations_and_failing_examples() -> None:
    """A5 Translations: MT never public anchor; private mt- never claim support; ht- fact only."""
    # User instruction 5 citation check:
    # docs/01_master_architecture.md §5.3 line 563: lang = lower, lower, [ lower ] ; (* "-x-mt" forbidden *)
    with pytest.raises(
        InvalidAnchorError, match="Machine translation is forbidden as an Expression"
    ):
        parse("wrk_01J9Z0123456789ABCDEFGHJKM/en-x-mt#p1")

    with pytest.raises(
        InvalidAnchorError, match="Machine translation is forbidden as an Expression"
    ):
        parse("wrk_01J9Z0123456789ABCDEFGHJKM/mt-en#p1")

    # Private mt- rendition is valid in syntax, but fails claim support check
    mt_priv = "pdoc_01J9Z0123456789ABCDEFGHJKM/v1.mt-en#p12"
    parsed_mt = parse(mt_priv)
    assert isinstance(parsed_mt, PrivateAnchor)
    assert parsed_mt.is_mt_rendition is True

    # Failing example: MT rendition used as claim support raises SemanticConstraintError
    with pytest.raises(SemanticConstraintError, match="MT_ANCHOR"):
        validate(mt_priv, is_claim_support=True)
    assert check_translation_support(mt_priv) is False

    # Certified translation ht- is allowed for RECORD_FACT claims
    ht_priv = "pdoc_01J9Z0123456789ABCDEFGHJKM/v1.ht-en#p12"
    validate(ht_priv, is_claim_support=True, claim_role="RECORD_FACT")
    assert check_translation_support(ht_priv, claim_role="RECORD_FACT") is True

    # Failing example: ht- cannot support PUBLIC_LAW claims
    with pytest.raises(SemanticConstraintError, match="support RECORD_FACT claims only"):
        validate(ht_priv, is_claim_support=True, claim_role="PUBLIC_LAW")
    assert check_translation_support(ht_priv, claim_role="PUBLIC_LAW") is False


def test_constraint_a6_canonical_match_key() -> None:
    """A6: canonical_key(anchor) = work_id "#" fragment (strips expr_key and o1. prefix)."""
    # Drops language expression key
    assert (
        canonical_key("wrk_01J9Z0123456789ABCDEFGHJKM/en#p45")
        == "wrk_01J9Z0123456789ABCDEFGHJKM#p45"
    )
    assert (
        canonical_key("wrk_01J9Z0123456789ABCDEFGHJKM/hi#ord")
        == "wrk_01J9Z0123456789ABCDEFGHJKM#ord"
    )

    # Drops default o1. prefix, but preserves non-default o2. prefix
    assert (
        canonical_key("wrk_01J9Z0123456789ABCDEFGHJKM/en#o1.p45")
        == "wrk_01J9Z0123456789ABCDEFGHJKM#p45"
    )
    assert (
        canonical_key("wrk_01J9Z0123456789ABCDEFGHJKM/en#o2.p14")
        == "wrk_01J9Z0123456789ABCDEFGHJKM#o2.p14"
    )

    # Drops statute expression key
    assert (
        canonical_key("wrk_01J9Z0123456789ABCDEFGHJKM/en@2003-02-06#sec-138.p1.c")
        == "wrk_01J9Z0123456789ABCDEFGHJKM#sec-138.p1.c"
    )

    # Provision ref stays as-is
    assert (
        canonical_key("wrk_01J9Z0123456789ABCDEFGHJKM#sec-302")
        == "wrk_01J9Z0123456789ABCDEFGHJKM#sec-302"
    )

    # PIT ref drops @date[~territory]
    assert (
        canonical_key("wrk_01J9Z0123456789ABCDEFGHJKM#sec-302@2023-12-31")
        == "wrk_01J9Z0123456789ABCDEFGHJKM#sec-302"
    )
    assert (
        canonical_key("wrk_01J9Z0123456789ABCDEFGHJKM#sec-3@2019-08-09~IN-UP")
        == "wrk_01J9Z0123456789ABCDEFGHJKM#sec-3"
    )

    # Private anchor drops version and rendition, strips o1.
    assert (
        canonical_key("pdoc_01J9Z0123456789ABCDEFGHJKM/v1#p12")
        == "pdoc_01J9Z0123456789ABCDEFGHJKM#p12"
    )
    assert (
        canonical_key("pdoc_01J9Z0123456789ABCDEFGHJKM/v2.mt-en#o1.p12")
        == "pdoc_01J9Z0123456789ABCDEFGHJKM#p12"
    )
    assert (
        canonical_key("pdoc_01J9Z0123456789ABCDEFGHJKM/v1#att2/p4")
        == "pdoc_01J9Z0123456789ABCDEFGHJKM#att2/p4"
    )

    # 01 §5.3 line 637: canonical_key ONLY strips expression key and default o1. prefix.
    # It must NEVER sort or reorder segments or path components.
    complex_statute = "wrk_01J9Z0123456789ABCDEFGHJKM/en@2024-07-01#sch-1.ord-39.rule-2A"
    assert canonical_key(complex_statute) == "wrk_01J9Z0123456789ABCDEFGHJKM#sch-1.ord-39.rule-2A"

    deep_para = "wrk_01J9Z0123456789ABCDEFGHJKM/en#p45.2.a.u1.x1"
    assert canonical_key(deep_para) == "wrk_01J9Z0123456789ABCDEFGHJKM#p45.2.a.u1.x1"

    sheet_table = "pdoc_01J9Z0123456789ABCDEFGHJKM/v1#sheet2.r15.c4"
    assert canonical_key(sheet_table) == "pdoc_01J9Z0123456789ABCDEFGHJKM#sheet2.r15.c4"


def test_constraint_a7_ial_rewriting_and_failing_example() -> None:
    """A7: IAL rewrites statute anchor to target expression valid on query valid_at."""
    statute_anchor = "wrk_01J9Z0123456789ABCDEFGHJKM/en@2003-02-06#sec-138.p1"
    rewritten = rewrite_statute_expression(statute_anchor, "en@2024-07-01~IN")
    assert format(rewritten) == "wrk_01J9Z0123456789ABCDEFGHJKM/en@2024-07-01~IN#sec-138.p1"

    # Failing example: rewriting a judgment anchor fails SemanticConstraintError
    judgment_anchor = "wrk_01J9Z0123456789ABCDEFGHJKM/en#p45"
    with pytest.raises(SemanticConstraintError, match="Only statute anchors can be rewritten"):
        rewrite_statute_expression(judgment_anchor, "en@2024-07-01")


def test_constraint_a8_clause_hierarchy_tree_depth() -> None:
    """A8: Clause level is positional (tree depth), not lexical."""
    frag_str = "sec-138.1.a.i.p1.e1"
    hierarchy = get_clause_hierarchy(frag_str)
    assert len(hierarchy) == 5
    assert hierarchy[0].kind == "subsec"
    assert hierarchy[0].value == "1"
    assert hierarchy[1].kind == "clause"
    assert hierarchy[1].value == "a"
    assert hierarchy[2].kind == "clause"
    assert hierarchy[2].value == "i"
    assert hierarchy[3].kind == "proviso"
    assert hierarchy[3].value == "p1"
    assert hierarchy[4].kind == "explanation"
    assert hierarchy[4].value == "e1"
