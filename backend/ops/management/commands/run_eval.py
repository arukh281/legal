"""Management command to execute an evaluation suite through EvalRunner.

Usage:
  python manage.py run_eval --gold-set=gld_01M4MRF7M7GM9YBPW1PEB317AT
  python manage.py run_eval --case=evc_01M4MRF7M7GM9YBPW1PEB317AX
  python manage.py run_eval --dry-run
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from eval.runner import EvalRunner

from ops.models import GoldSet


class Command(BaseCommand):
    help = "Run an evaluation suite against the pipeline and record audited EvalRun"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--gold-set",
            type=str,
            default=None,
            help="Gold set ID to run (defaults to latest active gold set)",
        )
        parser.add_argument(
            "--case",
            type=str,
            default=None,
            help="Specific eval_case_id to run in isolation",
        )
        parser.add_argument(
            "--split",
            type=str,
            default=None,
            choices=["DEV", "EXAM", "TRAIN"],
            help="Filter suite by split (DEV, EXAM, TRAIN)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Execute evaluation and generate scorecard without persisting ops.eval_run",
        )
        parser.add_argument(
            "--fake",
            action="store_true",
            help="Use FakeModelAdapter (ep_fake_qa) for offline deterministic evaluation",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        gold_set_id = options.get("gold_set")
        case_id = options.get("case")
        split = options.get("split")
        dry_run = options.get("dry_run", False)
        use_fake = options.get("fake", False)

        endpoint_override = "ep_fake_qa" if use_fake else None

        if not gold_set_id:
            # Find latest gold set
            gs = GoldSet.objects.order_by("-created_at").first()
            if not gs:
                self.stderr.write(self.style.ERROR("No gold sets found in database. Load one first."))
                return
            gold_set_id = gs.gold_set_id

        self.stdout.write(
            f"[*] Starting EvalRunner for gold_set={gold_set_id} (case={case_id}, split={split}, dry_run={dry_run}, fake={use_fake})..."
        )

        runner = EvalRunner(endpoint_override=endpoint_override)
        eval_run, case_summaries, scorecard_md = runner.run_suite(
            gold_set_id=gold_set_id,
            split=split,
            specific_case_id=case_id,
            dry_run=dry_run,
            endpoint_override=endpoint_override,
        )

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(scorecard_md)
        self.stdout.write("=" * 80 + "\n")
        self.stdout.write(
            self.style.SUCCESS(
                f"[✓] Evaluation complete. Run ID: {eval_run.run_id} | Gate Decision: {eval_run.gate_decision}"
            )
        )
