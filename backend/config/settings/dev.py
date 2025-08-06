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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
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
# EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.yourhost.com')
# EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.getenv('EMAIL_USER')
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')
# DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@yourdomain.com')
# Development-specific settings

ACCOUNT_SIGNUP_FIELDS = ['username*', 'email*', 'password1*', 'password2*']
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_CONFIRM_EMAIL_ON_GET = False  # This makes the GET verify the user
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False

# Override URLs in confirmation emails to point to frontend:
ACCOUNT_CONFIRMATION_EMAIL_TEMPLATE = "account/email/email_confirmation_message.txt"

# Headless support: replace links in email templates with frontend URLs
HEADLESS_FRONTEND_URLS = {
  "account_confirm_email": "https://your-frontend.com/verify-email/{key}",
  "account_signup":      "https://your-frontend.com/signup",
  "account_reset_password": "https://your-frontend.com/reset-password",
  "account_reset_password_from_key": "https://your-frontend.com/reset-password-confirm/{key}",
}

HEADLESS_ONLY = False

CELERY_BROKER_URL = os.getenv('RABBITMQ_URL')
CELERY_RESULT_BACKEND = 'rpc://'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_BEAT_SCHEDULE = {
    'run-example-task-every-minute': {
        'task': 'app.tasks.example_task',
        'schedule': 60.0,
        'args': (),
    },
}