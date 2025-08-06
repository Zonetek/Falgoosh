import logging
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation

logger = logging.getLogger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_confirmation_email(self, email_address_pk):
    try:
        email_address = EmailAddress.objects.select_related("user").get(pk=email_address_pk)

        if not email_address.user:
            logger.warning(f"No user attached to EmailAddress: {email_address_pk}")
            return

        send_email_confirmation(request=None, user=email_address.user)
        logger.info(f"Confirmation email sent to: {email_address.email}")

    except ObjectDoesNotExist:
        logger.error(f"EmailAddress with pk={email_address_pk} does not exist.")
    except Exception as e:
        logger.exception(f"Unexpected error sending confirmation email for pk={email_address_pk}")
        raise self.retry(exc=e)
