"""Contract and unit tests for Gold Set Loader (Amendment 2a, 2b).

Normative requirements:
- Amendment 2a: gold_loader rejects any case whose expected quote is not an exact
  substring of its expected anchor's live text.
- Amendment 2b: Agent-authored cases: provenance SYNTHETIC, reviewed=false.
"""

from __future__ import annotations

import pytest
from django.db import transaction
from eval.gold_loader import (
    GoldLoaderError,
    load_gold_set_from_dict,
    validate_expected_quotes,
)

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from ops.models import EvalCase
from parse.models import Anchor, Work


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_gold_loader_rejects_non_substring_quote(db: None) -> None:
    """Amendment 2a: gold_loader MUST reject any case whose expected quote is not an exact substring."""
    with admin_db_context():
        with transaction.atomic(using="owner"):
            work = Work.objects.create(
                work_id=mint_id("wrk"),
                work_type="JUDGMENT",
                title="Test Corporation v. Union of India",
                status="ACTIVE",
            )
            anchor = Anchor.objects.create(
                anchor_id=f"{work.work_id}/en#p10",
                work_id=work.work_id,
                expression_key="en",
                fragment="p10",
                node_type="PARA",
                text="The Adjudicating Authority is required to examine merely the existence of a default.",
                text_hash="hash_p10",
                lang="en",
                is_authoritative_expression=True,
                state="LIVE",
                first_parse_id="par_test",
                last_parse_id="par_test",
            )

            # 1. Exact substring succeeds
            validate_expected_quotes(
                mint_id("evc"),
                {
                    "propositions": [
                        {
                            "anchor_id": anchor.anchor_id,
                            "quote": "examine merely the existence of a default",
                        }
                    ]
                },
            )

            # 2. Fabricated / hallucinated quote fails loudly
            with pytest.raises(GoldLoaderError, match="Expected quote is not an exact substring"):
                validate_expected_quotes(
                    mint_id("evc"),
                    {
                        "propositions": [
                            {
                                "anchor_id": anchor.anchor_id,
                                "quote": "The Adjudicating Authority must examine equity and fairness in all matters.",
                            }
                        ]
                    },
                )


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_gold_loader_rejects_non_existent_anchor(db: None) -> None:
    """Amendment 2a: Expected anchor must exist and not be fabricated."""
    fake_anchor_id = "wrk_01FABRICATED000000000000/en#p99"
    with pytest.raises(GoldLoaderError, match="does not exist in plc.anchor"):
        validate_expected_quotes(
            mint_id("evc"),
            {
                "propositions": [
                    {
                        "anchor_id": fake_anchor_id,
                        "quote": "any quote",
                    }
                ]
            },
        )


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_gold_loader_enforces_synthetic_unreviewed_provenance(db: None) -> None:
    """Amendment 2b: Synthetic cases must have reviewed=False."""
    with admin_db_context():
        with transaction.atomic(using="owner"):
            work = Work.objects.create(
                work_id=mint_id("wrk"),
                work_type="JUDGMENT",
                title="Test In re Section 7",
                status="ACTIVE",
            )
            anchor = Anchor.objects.create(
                anchor_id=f"{work.work_id}/en#p1",
                work_id=work.work_id,
                expression_key="en",
                fragment="p1",
                node_type="PARA",
                text="A default occurred on the date specified in the demand notice.",
                text_hash="hash_p1",
                lang="en",
                is_authoritative_expression=True,
                state="LIVE",
                first_parse_id="par_test",
                last_parse_id="par_test",
            )

            gold_set_id = mint_id("gld")
            case_id = mint_id("evc")

            data = {
                "gold_set_id": gold_set_id,
                "name": "Synthetic Test Suite",
                "version": 1,
                "scope": "PUBLIC",
                "cases": [
                    {
                        "eval_case_id": case_id,
                        "version": 1,
                        "split": "DEV",
                        "task": "p6.qa_synthesis@1",
                        "strata": {"topic": "default"},
                        "input": {"question": "Did default occur?"},
                        "expected": {
                            "in_corpus": True,
                            "propositions": [
                                {
                                    "anchor_id": anchor.anchor_id,
                                    "quote": "default occurred on the date",
                                }
                            ],
                        },
                        "provenance": {
                            "source": "SYNTHETIC",
                            "author": "agent",
                            # Note: reviewed not explicitly provided -> loader must set to False
                        },
                    }
                ],
            }

            gold_set = load_gold_set_from_dict(data)
            assert gold_set.gold_set_id == gold_set_id

            loaded_case = EvalCase.objects.get(eval_case_id=case_id)
            assert loaded_case.provenance["source"] == "SYNTHETIC"
            assert loaded_case.provenance["reviewed"] is False


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_gold_loader_rejects_malformed_ids(db: None) -> None:
    """Validate that invalid Crockford ULIDs or invalid prefixes raise GoldLoaderError."""
    # Invalid gold set prefix
    with pytest.raises(GoldLoaderError, match="must start with gld_"):
        load_gold_set_from_dict({"gold_set_id": "bad_01M41234567890123456789012"})

    # Invalid Crockford characters (e.g. contains 'I' or 'L' or lowercase)
    with pytest.raises(GoldLoaderError):
        load_gold_set_from_dict({"gold_set_id": "gld_01M4INVALIDCROCKFORD00000"})
