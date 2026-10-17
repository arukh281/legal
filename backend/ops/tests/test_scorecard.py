"""Unit tests for Audited Markdown Scorecard Generator (Amendment 2c).

Normative requirements:
- Amendment 2c: No CIs or PROMOTE/REJECT below n=30; report counts and n.
  Only zero-tolerance checks (fabricated anchors, unmapped tombstones, ungrounded claims)
  can fail a run.
"""

from __future__ import annotations

import datetime

from eval.scorecard import generate_markdown_scorecard

from ops.models import EvalRun, GoldSet


def test_scorecard_preview_banner_below_n_30() -> None:
    """Amendment 2c: When n < 30, scorecard must show PREVIEW banner with counts and n."""
    gold_set = GoldSet(
        gold_set_id="gld_01M4TESTGOLDSET0000000000",
        name="Test Suite",
        version=1,
        scope="PUBLIC",
    )
    eval_run = EvalRun(
        run_id="evr_01M4TESTEVALRUN0000000000",
        gold_set=gold_set,
        candidate={"pipeline_version": "p6.qa_synthesis@1"},
        metrics={
            "n": 10,
            "n_reviewed": 0,
            "n_synthetic_unreviewed": 10,
            "passed_cases": 10,
            "avg_proposition_recall": 1.0,
            "zero_tolerance": {
                "fabricated_anchors": 0,
                "unmapped_tombstones": 0,
                "ungrounded_claims": 0,
                "sentinel_leaks": 0,
            },
        },
        gate_decision="PREVIEW",
        created_at=datetime.datetime(2026, 10, 11, 12, 0, 0, tzinfo=datetime.UTC),
    )

    cases = [
        {
            "eval_case_id": f"evc_01TESTCASE{i:016d}",
            "split": "DEV",
            "task": "p6.qa_synthesis@1",
            "passed": True,
            "score": 1.0,
            "reasons": [],
            "gate_checks": {
                "fabricated_anchors": 0,
                "unmapped_tombstones": 0,
                "ungrounded_claims": 0,
                "sentinel_leaks": 0,
            },
            "in_corpus_match": True,
        }
        for i in range(10)
    ]

    scorecard_md = generate_markdown_scorecard(eval_run, cases)

    assert "GATE DECISION: PREVIEW (n=10 < 30; reviewed=0)" in scorecard_md
    assert "Sample Size (n):** 10 (Reviewed: 0, Synthetic Unreviewed: 10)" in scorecard_md
    assert "Fabricated Anchors | 0 | 0 | PASS" in scorecard_md
    assert "Unmapped Tombstones | 0 | 0 | PASS" in scorecard_md
    assert "Ungrounded Claims (Shown) | 0 | 0 | PASS" in scorecard_md
    assert "Withheld Claims:" in scorecard_md


def test_scorecard_reject_banner_on_zero_tolerance_failure() -> None:
    """Amendment 2c: Zero tolerance failures MUST cause REJECT gate decision."""
    gold_set = GoldSet(
        gold_set_id="gld_01M4TESTGOLDSET0000000000",
        name="Test Suite",
        version=1,
        scope="PUBLIC",
    )
    eval_run = EvalRun(
        run_id="evr_01M4TESTEVALRUN0000000000",
        gold_set=gold_set,
        candidate={"pipeline_version": "p6.qa_synthesis@1"},
        metrics={
            "n": 10,
            "n_reviewed": 10,
            "n_synthetic_unreviewed": 0,
            "passed_cases": 9,
            "zero_tolerance": {
                "fabricated_anchors": 1,
                "unmapped_tombstones": 0,
                "ungrounded_claims": 0,
                "sentinel_leaks": 0,
            },
        },
        gate_decision="REJECT",
        created_at=datetime.datetime(2026, 10, 11, 12, 0, 0, tzinfo=datetime.UTC),
    )

    cases = [
        {
            "eval_case_id": "evc_01TESTCASE0000000000000001",
            "split": "DEV",
            "task": "p6.qa_synthesis@1",
            "passed": False,
            "score": 0.0,
            "reasons": ["FABRICATED_ANCHOR"],
            "gate_checks": {
                "fabricated_anchors": 1,
                "unmapped_tombstones": 0,
                "ungrounded_claims": 0,
                "sentinel_leaks": 0,
            },
            "in_corpus_match": True,
        }
    ]

    scorecard_md = generate_markdown_scorecard(eval_run, cases)
    assert "GATE DECISION: REJECT" in scorecard_md
    assert "Fabricated Anchors | 0 | 1 | FAIL" in scorecard_md


def test_scorecard_shows_adapter_and_model_at_top() -> None:
    """Item 1: Scorecard must display adapter (fake/real) and model(s) at top and in table."""
    gold_set = GoldSet(
        gold_set_id="gld_01M4TESTGOLDSET0000000000",
        name="Test Suite",
        version=1,
        scope="PUBLIC",
    )
    eval_run = EvalRun(
        run_id="evr_01M4TESTEVALRUN0000000000",
        gold_set=gold_set,
        candidate={
            "pipeline_version": "p6.reasoner@0.1.0|qa_synthesis_v1",
            "adapter": "real",
            "models": ["gemini-3.8-flash"],
            "endpoints": ["ep_gemini_3_8_flash"],
            "cases": {
                "evc_01TESTCASE0000000000000001": {
                    "endpoint_id": "ep_gemini_3_8_flash",
                    "model": "gemini-3.8-flash",
                }
            },
        },
        metrics={"n": 1, "passed_cases": 1, "zero_tolerance": {}},
        gate_decision="PREVIEW",
        created_at=datetime.datetime(2026, 10, 11, 12, 0, 0, tzinfo=datetime.UTC),
    )

    cases = [
        {
            "eval_case_id": "evc_01TESTCASE0000000000000001",
            "split": "DEV",
            "task": "p6.qa_synthesis@1",
            "model": "gemini-3.8-flash",
            "passed": True,
            "score": 1.0,
            "reasons": [],
            "gate_checks": {},
            "in_corpus_match": True,
        }
    ]

    scorecard_md = generate_markdown_scorecard(eval_run, cases)
    assert "- **Adapter:** `real`" in scorecard_md
    assert "- **Model(s):** gemini-3.8-flash (`ep_gemini_3_8_flash`)" in scorecard_md
    assert "| `evc_01TESTCASE0000000000000001` | DEV | `p6.qa_synthesis@1` | `gemini-3.8-flash` |" in scorecard_md

