"""Management command to configure database role credentials out-of-band.

Normative sources:
- Session S03 follow-up Directive #1: Passwords must not be hardcoded in migrations or git.
  Configure role credentials out of band from environment variables or Secrets Manager.
"""

from __future__ import annotations

import os
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


class Command(BaseCommand):
    help = (
        "Configure login credentials for PostgreSQL roles (app_rw, worker, admin_rw) out of band."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--database",
            default="owner" if "owner" in settings.DATABASES else "default",
            help="Database connection alias to use for altering roles (must have superuser/CREATEROLE).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        db_alias = options["database"]
        is_prod = not settings.DEBUG or getattr(settings, "ENVIRONMENT", "") == "production"

        app_rw_pwd = os.environ.get("POSTGRES_APP_RW_PASSWORD")
        worker_pwd = os.environ.get("POSTGRES_WORKER_PASSWORD")
        admin_rw_pwd = os.environ.get("POSTGRES_ADMIN_RW_PASSWORD")

        if is_prod:
            missing: list[str] = []
            if not app_rw_pwd:
                missing.append("POSTGRES_APP_RW_PASSWORD")
            if not worker_pwd:
                missing.append("POSTGRES_WORKER_PASSWORD")
            if not admin_rw_pwd:
                missing.append("POSTGRES_ADMIN_RW_PASSWORD")
            if missing:
                raise CommandError(
                    f"Production environment requires explicit role passwords: {', '.join(missing)}"
                )
            if app_rw_pwd == "app_rw" or worker_pwd == "worker" or admin_rw_pwd == "admin_rw":
                raise CommandError(
                    "Production environment cannot use default development passwords."
                )
        else:
            # Local dev & test default fallbacks
            app_rw_pwd = app_rw_pwd or "app_rw"
            worker_pwd = worker_pwd or "worker"
            admin_rw_pwd = admin_rw_pwd or "admin_rw"

        role_configs = [
            ("app_rw", app_rw_pwd),
            ("worker", worker_pwd),
            ("admin_rw", admin_rw_pwd),
        ]

        connection = connections[db_alias]
        with connection.cursor() as cursor:
            for role_name, password in role_configs:
                # Use parameterized query format via psycopg/PostgreSQL SQL identifier
                cursor.execute(
                    f"ALTER ROLE {role_name} WITH LOGIN PASSWORD %s;",
                    [password],
                )
                self.stdout.write(self.style.SUCCESS(f"Configured LOGIN for role '{role_name}'."))

        self.stdout.write(
            self.style.SUCCESS(
                "All runtime database roles successfully configured with credentials."
            )
        )
