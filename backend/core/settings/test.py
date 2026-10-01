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
DATABASES["default"]["TEST"] = {  # noqa: F405
    "NAME": os.environ.get("POSTGRES_TEST_DB", "test_lawyer_brain"),
}

# Dev-only authentication backend enabled for testing
DEV_AUTH_ENABLED = True
AUTHENTICATION_BACKENDS = [  # noqa: F405
    "core.auth.DevAuthenticationBackend",
    *AUTHENTICATION_BACKENDS,  # noqa: F405
]
