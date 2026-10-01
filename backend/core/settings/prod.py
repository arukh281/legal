"""Production settings for lawyer_brain."""

import os

from core.settings.base import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Dev authentication is strictly disabled in production
DEV_AUTH_ENABLED = False
AUTHENTICATION_BACKENDS = [
    b
    for b in AUTHENTICATION_BACKENDS  # noqa: F405
    if b != "core.auth.DevAuthenticationBackend"
]

# Enforce that runtime role is app_rw and not superuser/BYPASSRLS (Directive #3)
ENFORCE_RUNTIME_DB_ROLE_CHECK = True
