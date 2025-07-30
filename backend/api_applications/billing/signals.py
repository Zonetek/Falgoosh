from django.db.models.signals import post_save
from django.dispatch import receiver
from api_applications.shared_models.models.billing import PurchaseHistory, Invoice
from invoices import generate_invoice
from django.utils import timezone
import uuid
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PurchaseHistory)
def create_invoice_on_success(sender, instance, created, **kwargs):
    """Create an invoice when a purchase is successful."""
    try:
        if created and instance.success:
            num = f"INV-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
            response = generate_invoice(instance, num)
            if response.status_code == 201:
                Invoice.objects.create(
                    user=instance.user,
                    purchase=instance,
                    invoice_number=num,
                    pdf=response.data
                )

    except Exception as e:
        logger.error(f"Error creating invoice for purchase {instance.id}: {e}")
