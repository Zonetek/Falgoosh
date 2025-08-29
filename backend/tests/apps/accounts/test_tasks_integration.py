import time
import pytest
from django.core import mail
from api_applications.accounts.tasks import send_confirmation_email

pytestmark = [pytest.mark.django_db, pytest.mark.celery]


def wait_for_task(task_result, timeout=5):
    """Wait for Celery task to complete or timeout."""
    start = time.time()
    while not task_result.ready():
        if time.time() - start > timeout:
            raise TimeoutError("Task did not complete in time.")
        time.sleep(0.1)
    return task_result


def test_send_confirmation_email_triggers_email(celery_worker, email_address):
    initial_outbox_count = len(mail.outbox)

    task_result = send_confirmation_email.delay(email_address.pk)
    task_result = wait_for_task(task_result)

    assert task_result.successful()

    # Check an email was actually sent
    assert len(mail.outbox) == initial_outbox_count + 1
    sent_email = mail.outbox[-1]
    assert email_address.email in sent_email.to
    assert "confirm" in sent_email.subject.lower()
