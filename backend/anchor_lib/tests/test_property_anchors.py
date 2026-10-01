"""Hypothesis property tests for Anchor Grammar v1.1 and PostgreSQL domain alignment.

Normative sources:
- docs/01_master_architecture.md §5.3
- docs/01a_spine_decision_record.md (D8, D22.2)
- docs/mvp/03_data_model_and_contracts.md §1 item 3
"""

from __future__ import annotations

import random
import re
from typing import Any

import hypothesis.strategies as st
import pytest
from django.db import DatabaseError, connection
from hypothesis import given, settings

from anchor_lib.anchors import (
    InvalidAnchorError,
    format,
    is_private,
    is_public,
    parse,
)
from anchor_lib.ids import CROCKFORD_ALPHABET

# Verbatim PostgreSQL Domain Regexes from 03 §1 item 3
PUBLIC_ANCHOR_DB_REGEX = re.compile(
    r"^wrk_[0-9A-HJKMNP-TV-Z]{26}(/[a-z]{2,3}(\.r[1-9][0-9]*|@[0-9]{4}-[0-9]{2}-[0-9]{2}(~IN(-[A-Z]{2,3})?)?)?)?#[a-z0-9][A-Za-z0-9.\-]*(@[0-9]{4}-[0-9]{2}-[0-9]{2}(~IN(-[A-Z]{2,3})?)?)?$"
)
PRIVATE_ANCHOR_DB_REGEX = re.compile(
    r"^pdoc_[0-9A-HJKMNP-TV-Z]{26}/v[1-9][0-9]*(\.(mt|ht)-[a-z]{2,3})?#(att[1-9][0-9]*/)?[A-Za-z0-9.:\-]+$"
)
ANY_ANCHOR_DB_REGEX = re.compile(r"^(wrk|pdoc)_[0-9A-HJKMNP-TV-Z]{26}[/#]")

# ==============================================================================
# Hypothesis Strategies for Valid Anchor Generation
# ==============================================================================

ulid_chars = list(CROCKFORD_ALPHABET)
ulid_strategy = st.text(alphabet=ulid_chars, min_size=26, max_size=26)
posint_strategy = st.integers(min_value=1, max_value=9999)
lang_strategy = st.sampled_from(["en", "hi", "te", "bn", "mr", "ta", "gu", "kn"])
date_strategy = st.dates(
    min_value=st.dates().example().replace(year=1950, month=1, day=1),
    max_value=st.dates().example().replace(year=2030, month=12, day=31),
).map(lambda d: d.isoformat())
territory_strategy = st.sampled_from(["IN", "IN-UP", "IN-DEL", "IN-MH", "IN-KA", "IN-WB"])

# Judgment fragment strategy
sub_seg_strategy = st.one_of(
    st.integers(min_value=1, max_value=50).map(str),
    st.sampled_from(["a", "b", "c", "aa"]),
    st.integers(min_value=1, max_value=10).map(lambda n: f"u{n}"),
    st.integers(min_value=1, max_value=10).map(lambda n: f"x{n}"),
)


@st.composite
def judgment_frag_strategy(draw: Any) -> str:
    has_op = draw(st.booleans())
    op_num = draw(st.integers(min_value=1, max_value=9))
    op_prefix = f"o{op_num}." if has_op else ""

    kind = draw(st.sampled_from(["hdr", "ord", "fn", "para"]))
    if kind == "hdr":
        return f"{op_prefix}hdr"
    if kind == "ord":
        return f"{op_prefix}ord"
    if kind == "fn":
        return f"{op_prefix}fn{draw(posint_strategy)}"

    para_kind = draw(st.sampled_from(["p", "u"]))
    para_no = draw(posint_strategy)
    segs = draw(st.lists(sub_seg_strategy, max_size=2))
    has_sentence = draw(st.booleans())
    sentence = f".s{draw(posint_strategy)}" if has_sentence else ""
    seg_str = ("." + ".".join(segs)) if segs else ""
    return f"{op_prefix}{para_kind}{para_no}{seg_str}{sentence}"


# Statute fragment strategy
unit_no_strategy = st.one_of(
    posint_strategy.map(str),
    st.tuples(posint_strategy, st.sampled_from(["A", "B", "AA"])).map(lambda t: f"{t[0]}{t[1]}"),
)

stat_seg_strategy = st.one_of(
    posint_strategy.map(str),
    st.sampled_from(["a", "b", "c", "i", "iv"]),
    posint_strategy.map(lambda n: f"p{n}"),
    posint_strategy.map(lambda n: f"e{n}"),
    st.sampled_from(["ill-a", "ill-1"]),
)


@st.composite
def statute_frag_strategy(draw: Any) -> str:
    unit_type = draw(st.sampled_from(["sec", "art", "rule", "sch"]))
    unit_no = draw(unit_no_strategy)
    if unit_type == "sch":
        sch_variant = draw(st.sampled_from(["bare", "item", "ord_only", "ord_rule"]))
        if sch_variant == "item":
            unit = f"sch-{unit_no}.item-{draw(unit_no_strategy)}"
        elif sch_variant == "ord_only":
            unit = f"sch-{unit_no}.ord-{draw(unit_no_strategy)}"
        elif sch_variant == "ord_rule":
            unit = f"sch-{unit_no}.ord-{draw(unit_no_strategy)}.rule-{draw(unit_no_strategy)}"
        else:
            unit = f"sch-{unit_no}"
    else:
        unit = f"{unit_type}-{unit_no}"

    segs = draw(st.lists(stat_seg_strategy, max_size=2))
    if segs:
        return unit + "." + ".".join(segs)
    return unit


# Public anchor strategies
@st.composite
def public_anchor_strategy(draw: Any) -> str:
    work_id = f"wrk_{draw(ulid_strategy)}"
    expr_kind = draw(st.sampled_from(["judgment", "statute"]))
    lang = draw(lang_strategy)
    if expr_kind == "judgment":
        corrigendum = draw(st.booleans())
        expr = f"{lang}.r{draw(posint_strategy)}" if corrigendum else lang
        frag = draw(judgment_frag_strategy())
    else:
        has_terr = draw(st.booleans())
        terr = f"~{draw(territory_strategy)}" if has_terr else ""
        expr = f"{lang}@{draw(date_strategy)}{terr}"
        frag = draw(statute_frag_strategy())

    return f"{work_id}/{expr}#{frag}"


@st.composite
def provision_ref_strategy(draw: Any) -> str:
    work_id = f"wrk_{draw(ulid_strategy)}"
    frag = draw(statute_frag_strategy())
    return f"{work_id}#{frag}"


@st.composite
def pit_ref_strategy(draw: Any) -> str:
    work_id = f"wrk_{draw(ulid_strategy)}"
    frag = draw(statute_frag_strategy())
    date = draw(date_strategy)
    has_terr = draw(st.booleans())
    terr = f"~{draw(territory_strategy)}" if has_terr else ""
    return f"{work_id}#{frag}@{date}{terr}"


# Private anchor strategies
@st.composite
def private_anchor_strategy(draw: Any) -> str:
    pdoc_id = f"pdoc_{draw(ulid_strategy)}"
    ver = draw(posint_strategy)
    rend_kind = draw(st.sampled_from(["none", "mt", "ht"]))
    rend = ""
    if rend_kind != "none":
        rend = f".{rend_kind}-{draw(lang_strategy)}"

    has_att = draw(st.booleans())
    att = f"att{draw(posint_strategy)}/" if has_att else ""

    node_kind = draw(st.sampled_from(["para", "msg", "cell", "time", "rg", "hdr"]))
    if node_kind == "para":
        frag = draw(judgment_frag_strategy())
    elif node_kind == "msg":
        has_msg_att = draw(st.booleans())
        frag = (
            f"m{draw(posint_strategy)}.att{draw(posint_strategy)}"
            if has_msg_att
            else f"m{draw(posint_strategy)}"
        )
    elif node_kind == "cell":
        has_sheet = draw(st.booleans())
        sheet = f"sheet{draw(posint_strategy)}." if has_sheet else ""
        frag = f"{sheet}r{draw(posint_strategy)}.c{draw(posint_strategy)}"
    elif node_kind == "time":
        frag = "t00:03:15-00:03:40"
    elif node_kind == "rg":
        frag = f"pg{draw(posint_strategy)}.rg{draw(posint_strategy)}"
    else:
        frag = f"hdr.{draw(st.sampled_from(['from', 'to', 'cc', 'date', 'subject']))}"

    return f"{pdoc_id}/v{ver}{rend}#{att}{frag}"


all_valid_anchors_strategy = st.one_of(
    public_anchor_strategy(),
    provision_ref_strategy(),
    pit_ref_strategy(),
    private_anchor_strategy(),
)


# ==============================================================================
# Property Tests
# ==============================================================================


@settings(max_examples=100)
@given(anchor=all_valid_anchors_strategy)
def test_hypothesis_valid_anchors_roundtrip(anchor: str) -> None:
    """Hypothesis test: random valid anchors round-trip format(parse(a)) == a."""
    parsed = parse(anchor)
    assert format(parsed) == anchor


@settings(max_examples=100)
@given(anchor=all_valid_anchors_strategy)
def test_hypothesis_library_and_db_regex_never_disagree_on_valid_anchor(anchor: str) -> None:
    """Hypothesis test: library and DB regex never disagree on a valid anchor.

    User prompt: 'the library and DB regex never disagree on a valid anchor
    (library stricter is OK, looser is not)'.
    """
    assert ANY_ANCHOR_DB_REGEX.match(anchor) is not None, (
        f"any_anchor_ref rejected valid anchor: {anchor}"
    )

    if is_public(anchor):
        assert PUBLIC_ANCHOR_DB_REGEX.match(anchor) is not None, (
            f"public_anchor_ref DB domain regex rejected valid public anchor: {anchor}"
        )
    elif is_private(anchor):
        assert PRIVATE_ANCHOR_DB_REGEX.match(anchor) is not None, (
            f"private_anchor_ref DB domain regex rejected valid private anchor: {anchor}"
        )


@settings(max_examples=100)
@given(anchor=all_valid_anchors_strategy)
def test_hypothesis_random_mutations_rejected(anchor: str) -> None:
    """Hypothesis test: random corruptions/mutations are rejected by anchor_lib."""
    # Apply a destructive mutation
    mutation_type = random.choice(
        [
            "corrupt_prefix",
            "inject_bad_char",
            "break_ulid",
            "remove_hash",
            "bad_mt_expr",
        ]
    )

    mutated = anchor
    if mutation_type == "corrupt_prefix":
        mutated = "bad_" + anchor
    elif mutation_type == "inject_bad_char":
        pos = random.randint(0, len(anchor) - 1)
        mutated = anchor[:pos] + "!@#$" + anchor[pos:]
    elif mutation_type == "break_ulid":
        # truncate or insert invalid lowercase/O/I/L/U
        mutated = anchor.replace("0", "I").replace("A", "L")
    elif mutation_type == "remove_hash":
        mutated = anchor.replace("#", "/")
    elif mutation_type == "bad_mt_expr" and is_public(anchor):
        mutated = anchor.replace("/en", "/en-x-mt")

    if mutated != anchor:
        with pytest.raises((InvalidAnchorError, ValueError)):
            parse(mutated)


@pytest.mark.django_db
def test_live_postgres_domain_validation_and_rejection() -> None:
    """Test live PostgreSQL 18 domain constraints public_anchor_ref, private_anchor_ref, any_anchor_ref."""
    with connection.cursor() as cursor:
        # Create a temporary table with the three domains
        cursor.execute("""
            CREATE TEMP TABLE temp_anchor_test (
                id serial PRIMARY KEY,
                pub public_anchor_ref,
                priv private_anchor_ref,
                any_ref any_anchor_ref
            );
        """)

        # 1. Valid rows insert cleanly
        valid_pub = "wrk_01J9Z0123456789ABCDEFGHJKM/en#p45"
        valid_priv = "pdoc_01J9Z0123456789ABCDEFGHJKM/v1#p12"
        cursor.execute(
            "INSERT INTO temp_anchor_test (pub, priv, any_ref) VALUES (%s, %s, %s);",
            [valid_pub, valid_priv, valid_pub],
        )

        valid_pit = "wrk_01J9Z0123456789ABCDEFGHJKM#sec-302@2023-12-31"
        cursor.execute(
            "INSERT INTO temp_anchor_test (pub, priv, any_ref) VALUES (%s, %s, %s);",
            [valid_pit, valid_priv, valid_priv],
        )

        valid_sch = "wrk_01J9Z0123456789ABCDEFGHJKM/en@2024-07-01#sch-1.ord-8.rule-1"
        cursor.execute(
            "INSERT INTO temp_anchor_test (pub, priv, any_ref) VALUES (%s, %s, %s);",
            [valid_sch, valid_priv, valid_sch],
        )

        # 2. Mutated public anchor rejected by DB check constraint
        with pytest.raises(DatabaseError):
            cursor.execute(
                "INSERT INTO temp_anchor_test (pub) VALUES (%s);",
                ["wrk_INVALID_SHORT#p1"],
            )

        # 3. Private anchor into public_anchor_ref rejected
        with pytest.raises(DatabaseError):
            cursor.execute(
                "INSERT INTO temp_anchor_test (pub) VALUES (%s);",
                [valid_priv],
            )

        # 4. Public anchor into private_anchor_ref rejected
        with pytest.raises(DatabaseError):
            cursor.execute(
                "INSERT INTO temp_anchor_test (priv) VALUES (%s);",
                [valid_pub],
            )
