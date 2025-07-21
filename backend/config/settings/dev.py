import os
import sys

from dotenv import load_dotenv

from .base import (
    AUTH_USER_MODEL,
    AUTHENTICATION_BACKENDS,
    BASE_DIR,
    INSTALLED_APPS,
    MEDIA_ROOT,
    MEDIA_URL,
    MIDDLEWARE,
    REST_AUTH,
    REST_FRAMEWORK,
    ROOT_URLCONF,
    SIMPLE_JWT,
    SITE_ID,
    STATIC_ROOT,
    STATIC_URL,
    TEMPLATES,
    WSGI_APPLICATION,
)

load_dotenv()

DEBUG = True

SECRET_KEY = os.getenv("SECRET_KEY")

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT"),
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
