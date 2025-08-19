import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from api_applications.shared_models.models.billing import Invoice, PurchaseHistory

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PurchaseHistory)
def generate_invoice_on_purchase(sender, instance, created, **kwargs):
    """Create an invoice when a purchase is successful."""
    try:
        if created and not instance.invoice:
            instance.create_invoice()

    except Exception as e:
        logger.error(f"Error creating invoice for purchase {instance.id}: {e}")


@receiver(post_save, sender=Invoice)
def send_invoice_email(sender, instance, created, **kwargs):
    if created:  # Only send for new invoices
        send_mail(
            subject="Your Invoice",
            message=f"Dear {instance.user.username},\n\nThank you for your purchase.\nInvoice ID: {instance.id}\nAmount: {instance.amount} {instance.currency}\n\nBest regards,\nSupport Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.user.email],
            fail_silently=False,
        )
