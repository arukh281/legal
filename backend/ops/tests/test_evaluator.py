"""Unit and contract tests for DeterministicEvaluator (Amendments 2c, 2d).

Normative requirements:
- Amendment 2c: Only zero-tolerance checks (fabricated anchors, unmapped tombstones,
  ungrounded claims) can fail a run.
- Amendment 2d: Deterministic proposition matcher (expected anchor cited AND quote overlap);
  no LLM judge until a second model family is available.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from django.db import transaction
from eval.evaluator import DeterministicEvaluator, has_quote_overlap

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from parse.models import Anchor, Work
from reason.models import Claim


def test_has_quote_overlap() -> None:
    """Test deterministic quote overlap calculation."""
    # Substring containment
    assert has_quote_overlap("existence of a default", "required to examine merely the existence of a default under section 7")
    assert has_quote_overlap("section 14 moratorium applies to section 138", "section 14 moratorium applies to section 138 proceedings")

    # Significant token overlap
    eq = "proceedings under Section 138 against the corporate debtor are stayed"
    aq = "the Section 138 criminal proceedings against the corporate debtor remain covered by moratorium"
    assert has_quote_overlap(eq, aq)

    # Disjoint tokens
    assert not has_quote_overlap("limitation period is three years", "directors remain personally liable under section 141")
    assert not has_quote_overlap("", "some quote")


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_deterministic_evaluator_proposition_matching(db: None) -> None:
    """Amendment 2d: Proposition matches only when expected anchor is cited AND quote overlaps."""
    with admin_db_context():
        with transaction.atomic(using="owner"):
            work = Work.objects.create(
                work_id=mint_id("wrk"),
                work_type="JUDGMENT",
                title="P. Mohanraj v. Shah Brothers",
                status="ACTIVE",
            )
            anchor = Anchor.objects.create(
                anchor_id=f"{work.work_id}/en#p39",
                work_id=work.work_id,
                expression_key="en",
                fragment="p39",
                node_type="PARA",
                text="The moratorium under Section 14 applies to proceedings under Section 138 of the Negotiable Instruments Act against the corporate debtor.",
                text_hash="hash_p39",
                lang="en",
                is_authoritative_expression=True,
                state="LIVE",
                first_parse_id="par_test",
                last_parse_id="par_test",
            )

            evaluator = DeterministicEvaluator()

            expected = {
                "in_corpus": True,
                "propositions": [
                    {
                        "anchor_id": anchor.anchor_id,
                        "quote": "moratorium under Section 14 applies to proceedings under Section 138",
                        "topic": "Section 14 bar",
                    }
                ],
            }

            # 1. Matching claim: citations match expected anchor and quote overlaps
            matching_claim = Claim(
                claim_id=mint_id("clm"),
                text="Section 14 bars Section 138 NI Act proceedings against the corporate debtor.",
                support=[
                    {
                        "anchor_id": anchor.anchor_id,
                        "quote": "The moratorium under Section 14 applies to proceedings under Section 138",
                    }
                ],
            )
            res = evaluator.evaluate(
                case_id="evc_01TEST00000000000000000001",
                expected=expected,
                actual_output={"in_corpus": True},
                actual_claims=[matching_claim],
                verification_report=None,
            )
            assert res.passed is True
            assert res.score == 1.0
            assert len(res.matched_propositions) == 1

            # 2. Non-matching quote: citation matches anchor but quote does not overlap
            bad_quote_claim = Claim(
                claim_id=mint_id("clm"),
                text="Some claim.",
                support=[
                    {
                        "anchor_id": anchor.anchor_id,
                        "quote": "An entirely unrelated quote from another part of the paragraph.",
                    }
                ],
            )
            res_bad_quote = evaluator.evaluate(
                case_id="evc_01TEST00000000000000000001",
                expected=expected,
                actual_output={"in_corpus": True},
                actual_claims=[bad_quote_claim],
                verification_report=None,
            )
            assert len(res_bad_quote.matched_propositions) == 0
            assert len(res_bad_quote.unmatched_propositions) == 1


@pytest.mark.django_db(databases=["default", "admin", "owner"])
def test_evaluator_zero_tolerance_gates(db: None) -> None:
    """Amendment 2c: Zero-tolerance checks (fabricated anchors, unmapped tombstones, ungrounded claims)."""
    with admin_db_context():
        with transaction.atomic(using="owner"):
            work = Work.objects.create(
                work_id=mint_id("wrk"),
                work_type="JUDGMENT",
                title="Test Case",
                status="ACTIVE",
            )
            # Unmapped tombstone anchor
            unmapped_tombstone = Anchor.objects.create(
                anchor_id=f"{work.work_id}/en#p999",
                work_id=work.work_id,
                expression_key="en",
                fragment="p999",
                node_type="PARA",
                state="TOMBSTONED",
                forward_to=None,
                text="Old dissolved paragraph text.",
                text_hash="hash_p999",
                lang="en",
                is_authoritative_expression=True,
                first_parse_id="par_test",
                last_parse_id="par_test",
            )

            evaluator = DeterministicEvaluator()

            # Claim citing fabricated anchor
            fab_claim = Claim(
                claim_id=mint_id("clm"),
                text="Fabricated claim.",
                support=[{"anchor_id": "wrk_01NONEXISTENT000000000000/en#p1", "quote": "fake"}],
            )
            res_fab = evaluator.evaluate(
                case_id="evc_01TEST00000000000000000002",
                expected={"in_corpus": True, "propositions": []},
                actual_output={"in_corpus": True},
                actual_claims=[fab_claim],
                verification_report=None,
            )
            assert res_fab.passed is False
            assert res_fab.gate_checks["fabricated_anchors"] == 1

            # Claim citing unmapped tombstone
            tomb_claim = Claim(
                claim_id=mint_id("clm"),
                text="Tombstone claim.",
                support=[{"anchor_id": unmapped_tombstone.anchor_id, "quote": "dissolved"}],
            )
            res_tomb = evaluator.evaluate(
                case_id="evc_01TEST00000000000000000003",
                expected={"in_corpus": True, "propositions": []},
                actual_output={"in_corpus": True},
                actual_claims=[tomb_claim],
                verification_report=None,
            )
            assert res_tomb.passed is False
            assert res_tomb.gate_checks["unmapped_tombstones"] == 1

            # Withheld claim in verification report is NOT a zero-tolerance failure
            v_report = MagicMock()
            v_report.withheld_claim_ids = ["clm_01UNGROUNDED000000000000"]
            res_v = evaluator.evaluate(
                case_id="evc_01TEST00000000000000000004",
                expected={"in_corpus": True, "propositions": []},
                actual_output={"in_corpus": True},
                actual_claims=[],
                verification_report=v_report,
            )
            assert res_v.gate_checks["ungrounded_claims"] == 0
            assert res_v.withheld_claims == 1
            assert res_v.passed is True

            # Shown ungrounded claim (misquote) IS a zero-tolerance failure
            live_anchor = Anchor.objects.create(
                anchor_id=f"{work.work_id}/en#p1",
                work_id=work.work_id,
                expression_key="en",
                fragment="p1",
                node_type="PARA",
                state="LIVE",
                text="Exact text in live anchor for grounding test.",
                text_hash="hash_p1",
                lang="en",
                is_authoritative_expression=True,
                first_parse_id="par_test",
                last_parse_id="par_test",
            )
            shown_misquoted_claim = Claim(
                claim_id=mint_id("clm"),
                text="Claim with misquoted text.",
                support=[{"anchor_id": live_anchor.anchor_id, "quote": "completely fabricated non-existent quote"}],
            )
            res_shown_ungrounded = evaluator.evaluate(
                case_id="evc_01TEST00000000000000000005",
                expected={"in_corpus": True, "propositions": []},
                actual_output={"in_corpus": True},
                actual_claims=[shown_misquoted_claim],
                verification_report=None,
            )
            assert res_shown_ungrounded.passed is False
            assert res_shown_ungrounded.gate_checks["ungrounded_claims"] == 1
