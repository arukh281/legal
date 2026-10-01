from typing import Any

from django.apps import AppConfig
from django.db.backends.signals import connection_created


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
