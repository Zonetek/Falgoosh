from .base import (
    BASE_DIR,
    INSTALLED_APPS,
    MIDDLEWARE,
    STATIC_URL,
    STATIC_ROOT,
    MEDIA_ROOT,
    MEDIA_URL,
    ROOT_URLCONF,
    WSGI_APPLICATION,
    TEMPLATES,
    AUTH_USER_MODEL,
    AUTHENTICATION_BACKENDS,
    REST_FRAMEWORK,
    REST_AUTH,
    SIMPLE_JWT,
    SITE_ID,
)
import os
from dotenv import load_dotenv
import sys

load_dotenv()

DEBUG = True

SECRET_KEY = os.getenv("SECRET_KEY")

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR.parent / "db.sqlite3",
    }
}

# Testing configuration
TESTING = sys.argv[1:2] == ["test"]

# Debug toolbar settings - only if not testing
if not TESTING:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

INTERNAL_IPS = [
    "127.0.0.1",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development-specific settings
ACCOUNT_EMAIL_VERIFICATION = "none"
