"""Audited Markdown Scorecard Generator for Eval Runs.

Normative sources:
- docs/mvp/06_test_set_plan.md §6
- Session S08 Amendment 2(c):
  - No CIs or PROMOTE/REJECT below n=30; report counts and n.
  - Only zero-tolerance checks (fabricated anchors, unmapped tombstones,
    ungrounded claims) can fail a run.
"""

from __future__ import annotations

from typing import Any

from ops.models import EvalRun


def generate_markdown_scorecard(eval_run: EvalRun, case_evals: list[dict[str, Any]]) -> str:
    """Generate an audited Markdown scorecard for an evaluation run."""
    metrics = eval_run.metrics
    n = metrics.get("n", len(case_evals))
    passed_cases = metrics.get("passed_cases", 0)
    zt = metrics.get("zero_tolerance", {})

    fab_anchors = zt.get("fabricated_anchors", 0)
    unmap_tombs = zt.get("unmapped_tombstones", 0)
    ungrounded = zt.get("ungrounded_claims", 0)
    sentinels = zt.get("sentinel_leaks", 0)

    has_zt_violation = (fab_anchors + unmap_tombs + ungrounded + sentinels) > 0

    created_str = (
        eval_run.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        if eval_run.created_at
        else "In-Memory / Preview"
    )
    n_reviewed = metrics.get("n_reviewed", 0)
    n_synthetic = metrics.get("n_synthetic_unreviewed", n - n_reviewed)

    adapter_kind = eval_run.candidate.get("adapter", "unknown")
    models_list = eval_run.candidate.get("models", [])
    endpoints_list = eval_run.candidate.get("endpoints", [])
    if models_list and endpoints_list:
        models_str = ", ".join(f"{m} (`{ep}`)" for m, ep in zip(models_list, endpoints_list))
    elif models_list:
        models_str = ", ".join(models_list)
    elif "model" in eval_run.candidate:
        models_str = str(eval_run.candidate["model"])
    else:
        models_str = "N/A"

    lines: list[str] = [
        "# Evaluation Run Scorecard",
        f"- **Run ID:** `{eval_run.run_id}`",
        f"- **Gold Set:** `{eval_run.gold_set_id}`",
        f"- **Created At:** {created_str}",
        f"- **Candidate:** `{eval_run.candidate.get('pipeline_version', 'dev')}`",
        f"- **Adapter:** `{adapter_kind}`",
        f"- **Model(s):** {models_str}",
        f"- **Sample Size (n):** {n} (Reviewed: {n_reviewed}, Synthetic Unreviewed: {n_synthetic})",
        "",
        "## 1. Zero-Tolerance Gating Checks",
        "| Gate Check | Threshold | Actual Count | Status |",
        "|---|---|---|---|",
        f"| Fabricated Anchors | 0 | {fab_anchors} | {'PASS' if fab_anchors == 0 else 'FAIL'} |",
        f"| Unmapped Tombstones | 0 | {unmap_tombs} | {'PASS' if unmap_tombs == 0 else 'FAIL'} |",
        f"| Ungrounded / Withheld Claims | 0 | {ungrounded} | {'PASS' if ungrounded == 0 else 'FAIL'} |",
        f"| Sentinel Leaks | 0 | {sentinels} | {'PASS' if sentinels == 0 else 'FAIL'} |",
        "",
    ]

    # Gating Decision Rule (Amendments 2b, 2c)
    if has_zt_violation:
        banner = "> [!CAUTION]\n> **GATE DECISION: REJECT** — One or more zero-tolerance invariants failed."
    elif n_reviewed < 30:
        banner = (
            f"> [!NOTE]\n> **GATE DECISION: PREVIEW (n={n} < 30; reviewed={n_reviewed})**\n"
            "> Statistical confidence intervals and automated PROMOTE/REJECT thresholds "
            "are deferred until n >= 30. Agent-authored cases (SYNTHETIC, reviewed=false) "
            "are excluded from gate promotion decisions per Amendment 2b until lawyer review. "
            "All zero-tolerance gates are green."
        )
    else:
        banner = f"> [!TIP]\n> **GATE DECISION: PROMOTE** — n={n} >= 30 with zero-tolerance compliance."

    lines.extend([banner, "", "## 2. Metric Summary", f"- **Cases Passed:** {passed_cases} / {n}"])
    if "avg_proposition_recall" in metrics:
        lines.append(f"- **Mean Proposition Recall:** {metrics['avg_proposition_recall'] * 100:.1f}%")
    lines.extend(
        [
            "",
            "## 3. Case-by-Case Breakdown",
            "| Case ID | Split | Task | Model | In-Corpus | Score | ZT Violations | Verdict |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )

    for item in case_evals:
        cid = item.get("eval_case_id", "")
        split = item.get("split", "DEV")
        task = item.get("task", "")
        model_name = item.get("model", "N/A")
        in_corp = "Yes" if item.get("in_corpus_match", True) else "Mismatch"
        score = f"{item.get('score', 0.0):.2f}"
        zt_v = sum(item.get("gate_checks", {}).values())
        verdict = "PASS" if item.get("passed", False) else "FAIL"
        lines.append(
            f"| `{cid}` | {split} | `{task}` | `{model_name}` | {in_corp} | {score} | {zt_v} | {verdict} |"
        )

    lines.append("")
    return "\n".join(lines)
