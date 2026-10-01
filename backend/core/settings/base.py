"""Base settings for lawyer_brain."""

import os
from pathlib import Path

from dotenv import load_dotenv

from core.logging import setup_logging

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "insecure-s01-dev-key-lawyer-brain-phase1")
DEBUG = False
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,web").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "procrastinate.contrib.django",
    "ninja",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.microsoft",
    # Platform operations & schema owner
    "ops.apps.OpsConfig",
    # Blueprint Phase App Stubs
    "anchor_lib.apps.AnchorLibConfig",
    "ingest.apps.IngestConfig",
    "parse.apps.ParseConfig",
    "index.apps.IndexConfig",
    "kg.apps.KgConfig",
    "propagate.apps.PropagateConfig",
    "retrieve.apps.RetrieveConfig",
    "reason.apps.ReasonConfig",
    "rules.apps.RulesConfig",
    "workspace.apps.WorkspaceConfig",
    "verify.apps.VerifyConfig",
    "feedback.apps.FeedbackConfig",
    "surface.apps.SurfaceConfig",
    "gateway.apps.GatewayConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "core.middleware.TenantContextMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# 12-hour sessions per docs/mvp/04_stack_and_infra.md §2.10
SESSION_COOKIE_AGE = 43200

# django-allauth SSO configuration
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*"]
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
SOCIALACCOUNT_AUTO_SIGNUP = False
ACCOUNT_ADAPTER = "core.adapters.LawyerBrainAccountAdapter"
SOCIALACCOUNT_ADAPTER = "core.adapters.LawyerBrainSocialAccountAdapter"


ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# Database: PostgreSQL 18 with schemas plc, tpl, ops
DB_NAME = os.environ.get("POSTGRES_DB", "lawyer_brain")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {
            # Search path includes all three core schemas and public
            "options": "-c search_path=ops,plc,tpl,public",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Procrastinate task queue
PROCRASTINATE_APP = "procrastinate.contrib.django.app"

# Configure structured JSON logging
setup_logging(os.environ.get("LOG_LEVEL", "INFO"))

# Register system checks
import core.checks  # noqa: E402, F401
