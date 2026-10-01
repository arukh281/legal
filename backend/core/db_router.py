"""Database router for multi-role database architecture.

Normative sources:
- Session S03 follow-up Directive #1: Django Admin connects as admin_rw via dedicated alias.
- Session S03 follow-up Directive #3: Application code connects as app_rw; migrations run as owner.
"""

from __future__ import annotations

import contextvars
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

# ContextVar indicating that the current thread/task is executing an administrative operation
_is_admin_context: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "is_admin_context", default=False
)


@contextmanager
def admin_db_context() -> Generator[None]:
    """Context manager setting admin execution context for database routing."""
    token = _is_admin_context.set(True)
    try:
        yield
    finally:
        _is_admin_context.reset(token)


class DatabaseRouter:
    """Routes database operations across connection aliases:

    - 'admin': Django admin operations and cross-tenant platform administration
      (connects as admin_rw with BYPASSRLS).
    - 'owner': Database migrations and schema evolution (connects as postgres/migration owner).
    - 'default': Application web requests and tenant-scoped domain queries
      (connects as app_rw with NOBYPASSRLS).
    """

    def _is_admin(self, hints: dict[str, Any]) -> bool:
        if _is_admin_context.get():
            return True
        request = hints.get("request")
        if request and getattr(request, "path", "").startswith("/admin/"):
            return True
        return False

    def db_for_read(self, model: Any, **hints: Any) -> str | None:
        if self._is_admin(hints):
            return "admin"
        return "default"

    def db_for_write(self, model: Any, **hints: Any) -> str | None:
        if self._is_admin(hints):
            return "admin"
        return "default"

    def allow_relation(self, obj1: Any, obj2: Any, **hints: Any) -> bool:
        # All aliases point to the exact same physical PostgreSQL database instance
        return True

    def allow_migrate(
        self, db: str, app_label: str, model_name: str | None = None, **hints: Any
    ) -> bool | None:
        # Migrations must run on the owner connection alias (or default if owner is absent)
        if db == "owner":
            return True
        if db == "admin":
            return False
        # When migrating with standard manage.py migrate, allow default if owner alias not configured
        from django.conf import settings

        if "owner" not in settings.DATABASES:
            return True
        return db == "owner"
