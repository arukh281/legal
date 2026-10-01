"""Management command to export Django Ninja OpenAPI schema to a file."""

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from core.api import api


class Command(BaseCommand):
    help = "Export the Django Ninja OpenAPI schema to a JSON file"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--output",
            type=str,
            default="openapi.json",
            help="Path to output JSON file (default: openapi.json)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        output_path = Path(options["output"])
        schema = api.get_openapi_schema()
        output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        self.stdout.write(
            self.style.SUCCESS(f"Successfully exported OpenAPI schema to {output_path}")
        )
