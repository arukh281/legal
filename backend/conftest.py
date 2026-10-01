"""Pytest root configuration and database setup.

Normative source:
- Session S03 Directive #3: Dev and tests run as app_rw; migrations run as owner.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from django.db import connections
from django.test.utils import setup_databases, teardown_databases


@pytest.fixture(scope="session")
def django_db_setup(
    request: pytest.FixtureRequest,
    django_test_environment: None,
    django_db_blocker: Any,
    django_db_use_migrations: bool,
    django_db_keepdb: bool,
    django_db_createdb: bool,
    django_db_modify_db_settings: None,
) -> Generator[None]:
    """Sets up the test database using the owner connection, then binds app roles."""
    setup_databases_args: dict[str, Any] = {}
    if django_db_keepdb and not django_db_createdb:
        setup_databases_args["keepdb"] = True

    with django_db_blocker.unblock():
        # Setup test database and run migrations strictly via 'owner' (postgres)
        db_cfg = setup_databases(
            verbosity=request.config.option.verbose,
            interactive=False,
            aliases=["owner"],
            **setup_databases_args,
        )

        test_db_name = connections["owner"].settings_dict["NAME"]
        for alias in ("default", "admin", "worker"):
            connections[alias].settings_dict["NAME"] = test_db_name
            connections[alias].close()

    yield

    if not django_db_keepdb:
        with django_db_blocker.unblock():
            for alias in ("default", "admin", "worker"):
                connections[alias].close()
            # Terminate any remaining sessions to test DB from other connections/processes
            try:
                with connections["owner"].cursor() as cur:
                    cur.execute(
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid();",
                        [test_db_name],
                    )
            except Exception:
                pass
            for alias in ("default", "admin", "worker", "owner"):
                connections[alias].close()
            try:
                teardown_databases(db_cfg, verbosity=request.config.option.verbose)
            except Exception as exc:
                request.node.warn(
                    pytest.PytestWarning(f"Error when trying to teardown test databases: {exc!r}")
                )
