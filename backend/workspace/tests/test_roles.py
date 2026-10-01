"""Tests for PostgreSQL database roles (plc_writer, app_rw, worker) and runtime role checks.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §1 item 1: DB roles
- Session S03 Directive #3: plc_writer cannot read tpl; runtime role startup check
"""

from __future__ import annotations

from typing import Any

import pytest
from django.db import connection, transaction

from core.checks import check_runtime_db_role


def test_plc_writer_cannot_select_from_tpl(db: None) -> None:
    """plc_writer role is strictly forbidden from reading from schema tpl."""
    with connection.cursor() as cursor:
        cursor.execute("SET ROLE plc_writer;")
        try:
            with pytest.raises(Exception) as exc_info:
                with transaction.atomic():
                    cursor.execute("SELECT * FROM tpl.tenant LIMIT 1;")
            assert "permission denied for schema tpl" in str(exc_info.value).lower()
        finally:
            cursor.execute("RESET ROLE;")


def test_runtime_role_startup_check_flags_superuser_or_bypassrls(db: None, settings: Any) -> None:
    """Directive #3: Startup check refuses to boot web if runtime role is superuser or has BYPASSRLS."""
    settings.ENFORCE_RUNTIME_DB_ROLE_CHECK = True

    # When connected as test database owner (which is superuser postgres in dev container)
    errors = check_runtime_db_role()

    # Should detect superuser or bypassrls
    assert len(errors) > 0
    error_ids = {e.id for e in errors}
    assert "core.E003" in error_ids or "core.E004" in error_ids
