"""Local development settings for lawyer_brain."""

from core.settings.base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Dev-only authentication backend enabled for local dev
DEV_AUTH_ENABLED = True
AUTHENTICATION_BACKENDS = [  # noqa: F405
    "core.auth.DevAuthenticationBackend",
    *AUTHENTICATION_BACKENDS,  # noqa: F405
]
