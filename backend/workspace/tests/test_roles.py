"""Tests for PostgreSQL database roles (plc_writer, app_rw, worker) and runtime role checks.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §1 item 1: DB roles
- Session S03 Directive #3: plc_writer cannot read tpl; runtime role startup check
"""

from __future__ import annotations

from typing import Any

import pytest
from django.db import connections, transaction

from core.checks import check_runtime_db_role

pytestmark = pytest.mark.django_db(databases=["default", "owner", "admin", "worker"])


def test_plc_writer_cannot_select_from_tpl(db: None) -> None:
    """plc_writer role is strictly forbidden from reading from schema tpl."""
    with connections["owner"].cursor() as cursor:
        cursor.execute("SET ROLE plc_writer;")
        try:
            with pytest.raises(Exception) as exc_info:
                with transaction.atomic(using="owner"):
                    cursor.execute("SELECT * FROM tpl.tenant LIMIT 1;")
            assert "permission denied for schema tpl" in str(exc_info.value).lower()
        finally:
            cursor.execute("RESET ROLE;")


def test_runtime_role_startup_check_flags_superuser_or_bypassrls(db: None, settings: Any) -> None:
    """Directive #3: Startup check refuses to boot web if runtime role is superuser or has BYPASSRLS."""
    settings.ENFORCE_RUNTIME_DB_ROLE_CHECK = True

    # 1. When connected as owner (superuser postgres in test container), detects superuser
    errors_owner = check_runtime_db_role(using="owner")
    assert len(errors_owner) > 0
    error_ids = {e.id for e in errors_owner}
    assert "core.E003" in error_ids or "core.E004" in error_ids

    # 2. When connected as worker (which has BYPASSRLS), detects BYPASSRLS
    errors_worker = check_runtime_db_role(using="worker")
    assert any(e.id == "core.E004" for e in errors_worker)

    # 3. Default connection is app_rw (NOBYPASSRLS, non-superuser), passes cleanly
    errors_app_rw = check_runtime_db_role(using="default")
    assert len(errors_app_rw) == 0
