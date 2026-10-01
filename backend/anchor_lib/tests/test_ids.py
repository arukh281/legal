"""Tests for identifier minting, Crockford ULID monotonic generation, and prefix registry.

Normative sources:
- AGENTS.md §5 (prefixed Crockford ULID, no serial ints or standard UUIDs)
- docs/01_master_architecture.md §5.2 (ID prefix registry and form rules)
- docs/01a_spine_decision_record.md (D12, D16, D19.3, D20.5, D21.5, D21.16, D22.1)
- docs/mvp/03_data_model_and_contracts.md §1 item 2
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.apps import apps
from django.core.exceptions import ValidationError

from anchor_lib.ids import (
    MNEMONIC_PREFIXES,
    PREFIX_REGISTRY,
    is_valid_id,
    is_valid_sha256,
    mint_id,
    parse_id,
)
from anchor_lib.models import IDMinter, PrefixedULIDField


def test_prefix_registry_matches_docs_exactly() -> None:
    """Read docs/01_master_architecture.md §5.2 table and assert registry matches exactly.

    User instruction 1: Don't hand-type 64 prefixes from memory. Read the table in
    docs/01_master_architecture.md §5.2 (plus D-rulings) and assert the registry
    matches it exactly, with nothing missing and nothing extra.
    """
    doc_path = (
        Path(__file__).resolve().parent.parent.parent.parent / "docs" / "01_master_architecture.md"
    )
    assert doc_path.exists(), f"Doc path {doc_path} must exist"

    content = doc_path.read_text(encoding="utf-8")

    # Locate section 5.2
    s52_match = re.search(
        r"### 5\.2 ID prefix registry.*?\n(\| Prefix \|.*?\n\n)", content, re.DOTALL
    )
    assert s52_match is not None, "Could not find §5.2 prefix table in 01_master_architecture.md"
    table_text = s52_match.group(1)

    doc_prefixes: set[str] = set()
    for line in table_text.splitlines():
        line = line.strip()
        if not line.startswith("| `") or "Prefix" in line:
            continue
        # Extract the first column: e.g. | `wrk_` | or | `cm_`, `sm_`, `em_`, `ai_`, `cc_` ✱ |
        parts = line.split("|")
        if len(parts) < 3:
            continue
        col_prefix = parts[1]
        matches = re.findall(r"`([a-z0-9_]+):?`", col_prefix)
        for m in matches:
            clean = m.rstrip("_").rstrip(":")
            if clean and clean != "sha256":
                doc_prefixes.add(clean)

        # Check notes column for newly defined active prefixes mentioned (e.g. dgi_ digest item (public))
        notes_col = parts[5] if len(parts) > 5 else ""
        if "dgi_" in notes_col:
            doc_prefixes.add("dgi")

    # Assert exact match between doc prefixes and python registry
    missing_in_registry = doc_prefixes - PREFIX_REGISTRY
    extra_in_registry = PREFIX_REGISTRY - doc_prefixes
    assert not missing_in_registry, (
        f"Prefixes present in 01 §5.2 but missing in PREFIX_REGISTRY: {missing_in_registry}"
    )
    assert not extra_in_registry, (
        f"Prefixes in PREFIX_REGISTRY but missing in 01 §5.2: {extra_in_registry}"
    )
    assert PREFIX_REGISTRY == doc_prefixes


def test_mnemonic_prefixes_matches_doc_citation() -> None:
    """Assert MNEMONIC_PREFIXES matches docs/01_master_architecture.md §5.2 line 482.

    Docs line 482 states:
    "Curated reference registries may use stable upper-snake mnemonics after the prefix.
     These are crt_, ent_, rul_ and ter_, e.g. crt_IN_HC_ALL_LKO, ent_GOV_IN_UP, rul_IN_PREC_07."
    """
    doc_path = (
        Path(__file__).resolve().parent.parent.parent.parent / "docs" / "01_master_architecture.md"
    )
    content = doc_path.read_text(encoding="utf-8")
    m = re.search(
        r"These are `([a-z_]+)`,\s*`([a-z_]+)`,\s*`([a-z_]+)`\s*and\s*`([a-z_]+)`", content
    )
    assert m is not None, "Could not find mnemonic allowed prefixes sentence in 01 §5.2"
    matched_prefixes = {m.group(i).rstrip("_") for i in range(1, 5)}
    assert matched_prefixes == {"crt", "ent", "rul", "ter"}
    assert MNEMONIC_PREFIXES == matched_prefixes


def test_unknown_prefix_rejected() -> None:
    """Ensure mint_id rejects any unknown or unapproved prefix."""
    with pytest.raises(ValueError, match="Unknown prefix 'unknown'"):
        mint_id("unknown")

    with pytest.raises(ValueError, match="Unknown prefix 'foo'"):
        mint_id("foo")


def test_id_minting_monotonic_and_sorted_under_100k() -> None:
    """Ensure 100K IDs generated sequentially are unique and sorted matching creation order.

    Prompt requirement: 'IDs: uniqueness under 100K mints; sort order matches creation order'.
    """
    count = 100_000
    ids: list[str] = [mint_id("wrk") for _ in range(count)]

    # Uniqueness
    unique_ids = set(ids)
    assert len(unique_ids) == count, f"Expected {count} unique IDs, got {len(unique_ids)}"

    # Sort order matches creation order strictly
    assert ids == sorted(ids), "Generated monotonic ULIDs must be strictly sorted in creation order"


def test_registry_mnemonics_validation() -> None:
    """Validate curated reference registry mnemonics per 01 §5.2."""
    # Valid mnemonics
    assert is_valid_id("crt_IN_SC")
    assert is_valid_id("crt_IN_HC_DEL")
    assert is_valid_id("crt_IN_HC_ALL_LKO")
    assert is_valid_id("rul_IN_PREC_01")
    assert is_valid_id("rul_IN_PREC_24")
    assert is_valid_id("ent_GOV_IN_UP")
    assert is_valid_id("ter_IN_DL")

    parsed = parse_id("crt_IN_SC")
    assert parsed.prefix == "crt"
    assert parsed.is_mnemonic is True
    assert parsed.mnemonic == "IN_SC"

    # Works are NEVER mnemonic (wrk_ACT_NI is invalid; 01 §5.2 line 483)
    assert not is_valid_id("wrk_ACT_NI")
    with pytest.raises(ValueError, match="Works are never mnemonic"):
        parse_id("wrk_ACT_NI")

    # Other non-mnemonic prefixes reject mnemonics
    assert not is_valid_id("cas_CIVIL_APPEAL")
    assert not is_valid_id("ten_FIRM_ALPHA")

    # Lowercase or invalid characters in mnemonics rejected
    assert not is_valid_id("crt_sc")
    assert not is_valid_id("rul_in_prec_01")


def test_sha256_content_address_validation() -> None:
    """Validate sha256: content addresses (lowercase hex, 64 chars) per user instruction 8."""
    valid_sha = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert is_valid_sha256(valid_sha)
    assert is_valid_id(valid_sha)

    parsed = parse_id(valid_sha)
    assert parsed.prefix == "sha256"
    assert parsed.is_content_address is True

    # Uppercase hex rejected
    assert not is_valid_sha256(
        "sha256:E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"
    )
    # Wrong length rejected
    assert not is_valid_sha256("sha256:e3b0c442")
    assert not is_valid_sha256("sha256:" + "a" * 63)
    assert not is_valid_sha256("sha256:" + "a" * 65)


def test_prefixed_ulid_field_django_integration() -> None:
    """Test PrefixedULIDField default minting, validation, and deconstructibility."""
    # Test deconstructible IDMinter (User instruction 2)
    minter = IDMinter("wrk")
    minted = minter()
    assert minted.startswith("wrk_")
    assert is_valid_id(minted, prefix="wrk")

    # Field definition
    field = PrefixedULIDField(prefix="wrk", primary_key=True)
    name, path, args, kwargs = field.deconstruct()
    assert kwargs["prefix"] == "wrk"
    assert isinstance(kwargs["default"], IDMinter)
    assert kwargs["default"].prefix == "wrk"

    # Validation on save
    field.validate("wrk_01J9Z0123456789ABCDEFGHJKM", None)

    # Wrong prefix raises ValidationError
    with pytest.raises(ValidationError):
        field.validate("cas_01J9Z0123456789ABCDEFGHJKM", None)

    # Malformed ULID raises ValidationError
    with pytest.raises(ValidationError):
        field.validate("wrk_INVALID_SHORT", None)


def test_no_domain_model_has_autofield_or_uuid_pk() -> None:
    """Assert project-wide ID convention: no domain model in plc/tpl has an AutoField or UUID pk.

    User instruction 3: Add a test that fails if any domain model (plc/tpl) gets an
    integer or UUID primary key.
    """
    domain_app_labels = {
        "anchor_lib",
        "ingest",
        "parse",
        "index",
        "kg",
        "propagate",
        "retrieve",
        "reason",
        "rules",
        "workspace",
        "verify",
        "feedback",
        "surface",
        "gateway",
    }

    forbidden_pk_classes = {
        "AutoField",
        "BigAutoField",
        "SmallAutoField",
        "UUIDField",
    }

    for model in apps.get_models():
        app_label = model._meta.app_label
        table_name = model._meta.db_table

        # Check if model belongs to domain plane (plc.* or tpl.* or domain app)
        is_domain = (
            app_label in domain_app_labels
            or table_name.startswith("plc.")
            or table_name.startswith("tpl.")
        )
        if not is_domain:
            continue

        pk_field = model._meta.pk
        assert pk_field is not None, f"Model {model} must have a primary key"
        pk_class_name = pk_field.__class__.__name__

        assert pk_class_name not in forbidden_pk_classes, (
            f"Domain model {model} (table '{table_name}') has forbidden primary key "
            f"'{pk_class_name}'. AGENTS.md §5 and instruction 3 strictly require "
            "prefixed Crockford ULIDs (PrefixedULIDField), never auto integers or UUIDs."
        )
