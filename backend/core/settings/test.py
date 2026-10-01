"""Test settings for lawyer_brain.

Enforces execution against real PostgreSQL 18 + pgvector (per requirement #5).
"""

import os

from core.settings.base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Ensure tests run against PostgreSQL with search_path=ops,plc,tpl,public
# Owner is configured first so Django test runner creates/migrates test DB as postgres.
# default connects as app_rw (exercising RLS on every query); admin connects as admin_rw.
TEST_DB_NAME = os.environ.get("POSTGRES_TEST_DB", "test_lawyer_brain")

DATABASES = {
    "owner": {
        **DATABASES["owner"],  # noqa: F405
        "TEST": {
            "NAME": TEST_DB_NAME,
            "MIGRATE": True,
        },
    },
    "default": {
        **DATABASES["default"],  # noqa: F405
        "TEST": {
            "NAME": TEST_DB_NAME,
            "MIGRATE": False,
        },
    },
    "admin": {
        **DATABASES["admin"],  # noqa: F405
        "TEST": {
            "NAME": TEST_DB_NAME,
            "MIGRATE": False,
        },
    },
    "worker": {
        **DATABASES["worker"],  # noqa: F405
        "TEST": {
            "NAME": TEST_DB_NAME,
            "MIGRATE": False,
        },
    },
}

# Dev-only authentication backend enabled for testing
DEV_AUTH_ENABLED = True
AUTHENTICATION_BACKENDS = [  # noqa: F405
    "core.auth.DevAuthenticationBackend",
    *AUTHENTICATION_BACKENDS,  # noqa: F405
]
