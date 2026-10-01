from typing import Any

from django.apps import AppConfig
from django.db import models
from django.db.backends.signals import connection_created

# Patch Django's JSONField.from_db_value to gracefully handle already-deserialized dict/list from psycopg3
_original_from_db_value = models.JSONField.from_db_value


def _safe_from_db_value(self: Any, value: Any, expression: Any, connection: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    return _original_from_db_value(self, value, expression, connection)


models.JSONField.from_db_value = _safe_from_db_value  # type: ignore[method-assign]


def configure_postgres_connection(sender: Any, connection: Any, **kwargs: Any) -> None:
    """Register psycopg3 json/jsonb adapters on all PostgreSQL connections."""
    if connection.vendor == "postgresql" and connection.connection:
        from psycopg.types.json import register_default_adapters

        register_default_adapters(connection.connection)


class OpsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ops"

    def ready(self) -> None:
        # Connect connection configuration hook
        connection_created.connect(configure_postgres_connection)
        # Register demo chain steps for testing and local dev
        import ops.demo_chain  # noqa: F401
