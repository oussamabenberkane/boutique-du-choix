"""
Django settings for the boutique_de_choix project.

Designed to run on free shared hosting (SQLite), single currency (DZD),
single language (French). Configure secrets through environment
variables or a local .env file.
"""

import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", get_random_secret_key())

DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")
    if h.strip()
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "adminsortable2",
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.cart",
    "apps.orders",
    "apps.payments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.store_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "accounts.User"

# After admin logout, go back to the admin login page.
LOGOUT_REDIRECT_URL = "/admin/"

# The SQLite file location is environment-driven so it can be moved onto a
# writable volume at runtime (container filesystems are read-only).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get(
            "DB_PATH",
            Path(os.environ.get("DB_DIR", BASE_DIR)) / "db.sqlite3",
        ),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "fr"

LANGUAGES = [
    ("fr", "Français"),
]

TIME_ZONE = "Africa/Algiers"

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Chargily Pay (V2)
# ---------------------------------------------------------------------------
CHARGILY_KEY = os.environ.get("CHARGILY_KEY", "")
CHARGILY_SECRET = os.environ.get("CHARGILY_SECRET", "")
CHARGILY_URL = os.environ.get(
    "CHARGILY_URL", "https://pay.chargily.net/test/api/v2/"
)
# When True, checkout goes through a local "simulated" payment page so the
# whole flow can be tested without live credentials.
CHARGILY_FAKE = env_bool("CHARGILY_FAKE", True)


# ---------------------------------------------------------------------------
# Checkout / orders
# ---------------------------------------------------------------------------
SHIPPING_FLAT_RATE = int(os.environ.get("SHIPPING_FLAT_RATE", "600"))
SHIPPING_FREE_THRESHOLD = int(os.environ.get("SHIPPING_FREE_THRESHOLD", "10000"))

CURRENCY = "DZD"
CURRENCY_SYMBOL = os.environ.get("CURRENCY_SYMBOL", "DA")

STORE_NAME = os.environ.get("STORE_NAME", "Boutique de Choix")

# Domaine public du site (utilisé pour les URLs de retour Chargily).
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "http://localhost:8000")

# NATIONAL_PAYMENT_ON_DELIVERY toggles the cash-on-delivery option.
ALLOW_PAYMENT_ON_DELIVERY = env_bool("ALLOW_PAYMENT_ON_DELIVERY", True)