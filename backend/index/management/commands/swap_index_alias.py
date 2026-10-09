"""Management command to promote an index generation or rollback to a previous generation.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.5
- Session S06 Generation lifecycle
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError

from index.generations import promote_generation, rollback_generation


class Command(BaseCommand):
    help = "Promote or rollback an index generation alias atomically."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--family",
            type=str,
            default="plc_chunks",
            help="Index family to swap (default: plc_chunks).",
        )
        parser.add_argument(
            "--to-generation",
            type=str,
            help="Target generation to promote to LIVE.",
        )
        parser.add_argument(
            "--rollback",
            action="store_true",
            help="Rollback the alias to its previous generation.",
        )
        parser.add_argument(
            "--reason",
            type=str,
            default="PROMOTION",
            help="Reason for promotion / swap.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        family = options.get("family", "plc_chunks")
        to_gen = options.get("to_generation")
        do_rollback = options.get("rollback", False)
        reason = options.get("reason", "PROMOTION")

        if do_rollback:
            try:
                alias = rollback_generation(index_family=family)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully rolled back alias '{family}' to generation '{alias.generation}'."
                    )
                )
            except Exception as e:
                raise CommandError(f"Rollback failed: {e}") from e
        else:
            if not to_gen:
                raise CommandError("Must provide --to-generation when not using --rollback.")
            try:
                alias = promote_generation(
                    index_family=family,
                    to_generation=to_gen,
                    reason=reason,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully promoted generation '{to_gen}' to LIVE for family '{family}'."
                    )
                )
            except Exception as e:
                raise CommandError(f"Promotion failed: {e}") from e
