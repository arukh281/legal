"""Deterministic Evaluation Engine for Grounding and Proposition Matching.

Normative sources:
- docs/mvp/06_test_set_plan.md §1, §5, §6
- docs/10_P8_verification_evaluation.md §5.3, §5.10
- Session S08 Amendments 2(c) and 2(d):
  - Amendment 2(c): No CIs or PROMOTE/REJECT below n=30; report counts and n.
    Only zero-tolerance checks (fabricated anchors, unmapped tombstones,
    ungrounded claims) can fail a run.
  - Amendment 2(d): Deterministic proposition matcher (expected anchor cited AND
    quote overlap); no LLM judge until a second model family is available.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from parse.models import Anchor
from reason.models import Claim


def normalize_words(text: str) -> set[str]:
    """Tokenize and normalize text into words for overlap scoring."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return {w for w in cleaned.split() if len(w) > 2}


def has_quote_overlap(expected_quote: str, actual_quote: str) -> bool:
    """Check whether actual quote overlaps significantly with expected quote."""
    if not expected_quote or not actual_quote:
        return False

    eq_norm = " ".join(expected_quote.split()).lower()
    aq_norm = " ".join(actual_quote.split()).lower()

    # Exact or substring containment
    if eq_norm in aq_norm or aq_norm in eq_norm:
        return True

    # Token overlap Jaccard
    e_words = normalize_words(expected_quote)
    a_words = normalize_words(actual_quote)
    if not e_words or not a_words:
        return False

    intersection = e_words.intersection(a_words)
    smaller = min(len(e_words), len(a_words))
    # If at least 40% of the smaller quote's tokens match
    return (len(intersection) / smaller) >= 0.40


@dataclass
class CaseEvaluation:
    eval_case_id: str
    passed: bool
    score: float
    reasons: list[str] = field(default_factory=list)
    gate_checks: dict[str, int] = field(default_factory=dict)
    matched_propositions: list[dict[str, Any]] = field(default_factory=list)
    unmatched_propositions: list[dict[str, Any]] = field(default_factory=list)
    claims_evaluated: int = 0
    withheld_claims: int = 0
    in_corpus_match: bool = True


class DeterministicEvaluator:
    """Evaluates pipeline outputs deterministically without relying on model-based judges."""

    def evaluate(
        self,
        case_id: str,
        expected: dict[str, Any],
        actual_output: dict[str, Any],
        actual_claims: list[Claim],
        verification_report: Any,
    ) -> CaseEvaluation:
        reasons: list[str] = []
        gate_checks = {
            "fabricated_anchors": 0,
            "unmapped_tombstones": 0,
            "ungrounded_claims": 0,
            "sentinel_leaks": 0,
        }

        # Withheld claims are tracked separately; they are NOT a zero-tolerance failure.
        withheld_claim_ids: set[str] = set()
        if verification_report:
            withheld_claim_ids = set(getattr(verification_report, "withheld_claim_ids", []) or [])

        withheld_claims_count = len(withheld_claim_ids)
        if withheld_claims_count > 0:
            reasons.append(f"WITHHELD_CLAIMS_COUNT: {withheld_claims_count}")

        # 1. Zero-Tolerance Gate Checks on SHOWN Claims (not withheld)
        live_anchors: dict[str, Anchor] = {}
        for claim in actual_claims:
            is_shown = claim.claim_id not in withheld_claim_ids
            supports = claim.support if isinstance(claim.support, list) else []
            for s in supports:
                if not isinstance(s, dict):
                    continue
                a_id = s.get("anchor_id", "")
                anchor = Anchor.objects.filter(anchor_id=a_id).first()
                quote = str(s.get("quote", "")).strip()

                if is_shown:
                    # Zero Tolerance 1: Fabricated anchor in shown claim
                    if not anchor:
                        gate_checks["fabricated_anchors"] += 1
                        reasons.append(f"SHOWN_FABRICATED_ANCHOR: {a_id}")
                    else:
                        live_anchors[a_id] = anchor
                        # Zero Tolerance 2: Unmapped tombstone in shown claim
                        if anchor.state == "TOMBSTONED" and not anchor.forward_to:
                            gate_checks["unmapped_tombstones"] += 1
                            reasons.append(f"SHOWN_UNMAPPABLE_TOMBSTONE: {a_id}")
                        elif anchor.state == "TOMBSTONED" and anchor.forward_to:
                            fwd = Anchor.objects.filter(anchor_id=anchor.forward_to).first()
                            if not fwd or fwd.state != "LIVE":
                                gate_checks["unmapped_tombstones"] += 1
                                reasons.append(f"SHOWN_UNMAPPABLE_TOMBSTONE: {a_id}")

                        # Zero Tolerance 3: Ungrounded claim shown to user
                        target_text = anchor.text
                        if anchor.state == "TOMBSTONED" and anchor.forward_to:
                            fwd = Anchor.objects.filter(anchor_id=anchor.forward_to).first()
                            if fwd:
                                target_text = fwd.text
                        if quote and quote not in target_text:
                            gate_checks["ungrounded_claims"] += 1
                            reasons.append(f"SHOWN_UNGROUNDED_CLAIM_MISQUOTE: {claim.claim_id}")
                else:
                    if anchor:
                        live_anchors[a_id] = anchor

        # Check if any shown claim has an unsupported status in verification report
        if verification_report:
            verifications = getattr(verification_report, "claimverification_set", None)
            if verifications:
                for cv in verifications.all():
                    if cv.claim_id not in withheld_claim_ids and cv.status == "UNSUPPORTED":
                        gate_checks["ungrounded_claims"] += 1
                        reasons.append(f"SHOWN_UNSUPPORTED_CLAIM: {cv.claim_id}")

        # 2. In-Corpus Check
        expected_in_corpus = expected.get("in_corpus", True)
        actual_in_corpus = actual_output.get("in_corpus", True)
        in_corpus_match = expected_in_corpus == actual_in_corpus

        if not in_corpus_match:
            reasons.append(
                f"IN_CORPUS_MISMATCH: expected {expected_in_corpus}, got {actual_in_corpus}"
            )

        # If expected out of corpus
        if not expected_in_corpus:
            shown_claims_count = len([c for c in actual_claims if c.claim_id not in withheld_claim_ids])
            passed = (
                not actual_in_corpus
                and shown_claims_count == 0
                and gate_checks["fabricated_anchors"] == 0
                and gate_checks["unmapped_tombstones"] == 0
                and gate_checks["ungrounded_claims"] == 0
            )
            score = 1.0 if passed else 0.0
            return CaseEvaluation(
                eval_case_id=case_id,
                passed=passed,
                score=score,
                reasons=reasons,
                gate_checks=gate_checks,
                claims_evaluated=len(actual_claims),
                withheld_claims=withheld_claims_count,
                in_corpus_match=in_corpus_match,
            )

        # 3. Deterministic Proposition Matching (Amendment 2d)
        expected_props = expected.get("propositions", [])
        matched_props: list[dict[str, Any]] = []
        unmatched_props: list[dict[str, Any]] = []

        for p_idx, exp_prop in enumerate(expected_props):
            exp_anchor_id = exp_prop.get("anchor_id", "")
            exp_quote = exp_prop.get("quote", "")

            # Check if expected anchor resolves through forward pointer
            exp_anchor = Anchor.objects.filter(anchor_id=exp_anchor_id).first()
            valid_anchor_ids = {exp_anchor_id}
            if exp_anchor and exp_anchor.forward_to:
                valid_anchor_ids.add(exp_anchor.forward_to)

            prop_matched = False
            shown_claims = [c for c in actual_claims if c.claim_id not in withheld_claim_ids]
            for claim in shown_claims:
                supports = claim.support if isinstance(claim.support, list) else []
                for s in supports:
                    if not isinstance(s, dict):
                        continue
                    claim_a_id = s.get("anchor_id", "")
                    claim_quote = s.get("quote", "")

                    # Must match expected anchor AND have quote overlap
                    if claim_a_id in valid_anchor_ids and has_quote_overlap(exp_quote, claim_quote):
                        prop_matched = True
                        matched_props.append(
                            {
                                "prop_index": p_idx,
                                "expected_anchor": exp_anchor_id,
                                "claim_id": claim.claim_id,
                                "claim_text": claim.text,
                                "quote_overlap": True,
                            }
                        )
                        break
                if prop_matched:
                    break

            if not prop_matched:
                unmatched_props.append(
                    {
                        "prop_index": p_idx,
                        "expected_anchor": exp_anchor_id,
                        "expected_quote": exp_quote,
                        "topic": exp_prop.get("topic", ""),
                    }
                )

        total_props = len(expected_props)
        prop_recall = len(matched_props) / total_props if total_props > 0 else 1.0

        # Case pass rule
        has_zero_tolerance_failure = any(count > 0 for count in gate_checks.values())
        passed = (
            not has_zero_tolerance_failure
            and in_corpus_match
            and (total_props == 0 or prop_recall > 0.0)
        )
        score = prop_recall if not has_zero_tolerance_failure else 0.0

        return CaseEvaluation(
            eval_case_id=case_id,
            passed=passed,
            score=score,
            reasons=reasons,
            gate_checks=gate_checks,
            matched_propositions=matched_props,
            unmatched_propositions=unmatched_props,
            claims_evaluated=len(actual_claims),
            withheld_claims=withheld_claims_count,
            in_corpus_match=in_corpus_match,
        )
