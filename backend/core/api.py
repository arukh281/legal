"""Django Ninja API configuration and health endpoint."""

from datetime import UTC, datetime
from typing import Any

from django.db import connection
from ninja import NinjaAPI, Schema

api = NinjaAPI(
    title="Lawyer Brain API",
    version="1.0.0",
    description="Corporate-law legal intelligence platform API",
    urls_namespace="api",
)


class HealthResponse(Schema):
    status: str
    database: str
    schemas: list[str]
    timestamp: str


@api.get("/health", response=HealthResponse, tags=["Health"])
def health_check(request: Any) -> dict[str, Any]:
    """Health check validating database connectivity and schema existence."""
    schemas_found: list[str] = []
    db_status = "connected"

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name IN ('plc', 'tpl', 'ops')
                ORDER BY schema_name;
                """
            )
            rows = cursor.fetchall()
            schemas_found = [r[0] for r in rows]
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
        "schemas": schemas_found,
        "timestamp": datetime.now(UTC).isoformat(),
    }
