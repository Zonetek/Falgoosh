import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", password="password")


@pytest.fixture
def email_address(db, user):
    return EmailAddress.objects.create(user=user, email=user.email, verified=False, primary=True)


@pytest.fixture(autouse=True, scope="session")
def configure_celery():
    from django.conf import settings
    settings.CELERY_TASK_ALWAYS_EAGER = False
    settings.CELERY_TASK_EAGER_PROPAGATES = False
