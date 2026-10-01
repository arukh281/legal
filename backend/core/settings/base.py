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
    "core.apps.CoreConfig",
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
    "core.admin_security.AdminSecurityMiddleware",
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
DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")

# app_rw connects application code subject to RLS (NOBYPASSRLS)
APP_DB_USER = os.environ.get("POSTGRES_APP_USER", "app_rw")
APP_DB_PASSWORD = os.environ.get("POSTGRES_APP_PASSWORD", "app_rw")

# postgres owner connection for schema migrations and DDL
OWNER_DB_USER = os.environ.get("POSTGRES_OWNER_USER", os.environ.get("POSTGRES_USER", "postgres"))
OWNER_DB_PASSWORD = os.environ.get(
    "POSTGRES_OWNER_PASSWORD", os.environ.get("POSTGRES_PASSWORD", "postgres")
)

# admin_rw connects Django admin for cross-tenant operations (BYPASSRLS)
ADMIN_DB_USER = os.environ.get("POSTGRES_ADMIN_USER", "admin_rw")
ADMIN_DB_PASSWORD = os.environ.get("POSTGRES_ADMIN_PASSWORD", "admin_rw")

# worker connects background jobs and asynchronous tasks (BYPASSRLS with scoped elevation)
WORKER_DB_USER = os.environ.get("POSTGRES_WORKER_USER", "worker")
WORKER_DB_PASSWORD = os.environ.get("POSTGRES_WORKER_PASSWORD", "worker")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": APP_DB_USER,
        "PASSWORD": APP_DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {
            # Search path includes all three core schemas and public
            "options": "-c search_path=ops,plc,tpl,public",
        },
    },
    "owner": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": OWNER_DB_USER,
        "PASSWORD": OWNER_DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {
            "options": "-c search_path=ops,plc,tpl,public",
        },
    },
    "admin": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": ADMIN_DB_USER,
        "PASSWORD": ADMIN_DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {
            "options": "-c search_path=ops,plc,tpl,public",
        },
    },
    "worker": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": WORKER_DB_USER,
        "PASSWORD": WORKER_DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {
            "options": "-c search_path=ops,plc,tpl,public",
        },
    },
}

DATABASE_ROUTERS = ["core.db_router.DatabaseRouter"]

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

# Crawler & Source Ingestion settings (Session S04 Directive #3)
CRAWLER_USER_AGENT = os.environ.get(
    "CRAWLER_USER_AGENT",
    "LegalIntelligenceBot/1.0 (+https://example.org/bot; contact@example.org)",
)
CRAWLER_CONTACT_EMAIL = os.environ.get("CRAWLER_CONTACT_EMAIL", "contact@example.org")

# Object Storage S3 / MinIO (docs/mvp/04_stack_and_infra.md §2.9)
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
S3_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
S3_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin")
S3_REGION = os.environ.get("AWS_REGION", "ap-south-1")
S3_RAW_BUCKET = os.environ.get("S3_RAW_BUCKET", "plc-raw")

# Configure structured JSON logging
setup_logging(os.environ.get("LOG_LEVEL", "INFO"))

# Register system checks
import core.checks  # noqa: E402, F401
