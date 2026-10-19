"""Wrapped migrate command enforcing --database=owner when owner database alias is configured."""

from typing import Any

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management.commands.migrate import Command as DjangoMigrateCommand


class Command(DjangoMigrateCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        database = options.get("database")
        if "owner" in settings.DATABASES and database != "owner":
            raise CommandError(
                "Plain 'manage.py migrate' is prohibited because migrations must run on the 'owner' database alias.\n"
                "Please run: python manage.py migrate --database=owner"
            )
        super().handle(*args, **options)
