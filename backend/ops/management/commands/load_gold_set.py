"""Management command: load_gold_set.

Loads and validates an evaluation gold set JSON fixture into ops.gold_set and ops.eval_case.

Normative sources:
- docs/mvp/06_test_set_plan.md §7
- Session S08 Amendments 2(a) and 2(b)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from eval.gold_loader import GoldLoaderError, load_gold_set_from_file


class Command(BaseCommand):
    help = "Loads and validates a gold evaluation set fixture."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "file_path",
            type=str,
            help="Path to the gold set JSON fixture file.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate without committing changes to database.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        file_path = options["file_path"]
        dry_run = options.get("dry_run", False)

        path = Path(file_path)
        if not path.is_file():
            raise CommandError(f"File not found: {file_path}")

        self.stdout.write(f"[*] Loading gold set from {path} (dry_run={dry_run})...")
        try:
            gold_set = load_gold_set_from_file(path, dry_run=dry_run)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully loaded and validated gold set {gold_set.gold_set_id} ({gold_set.name} v{gold_set.version})"
                )
            )
        except GoldLoaderError as e:
            raise CommandError(f"Gold set validation failure: {e}") from e
