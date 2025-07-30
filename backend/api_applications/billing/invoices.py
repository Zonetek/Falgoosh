import logging

from rest_framework import status
from rest_framework.response import Response

from api_applications.shared_models.models.billing import Invoice, PurchaseHistory

logger = logging.getLogger(__name__)


def generate_invoice(purchase: PurchaseHistory, invoice_number: str) -> Response:
    """Generate a invoice for a given purchase."""
    try:
        logger.info(f"Generating invoice metadata for purchase {purchase.pk}")

        invoice_data = {
            "invoice_number": invoice_number,
            "date": purchase.timestamp.strftime("%Y-%m-%d"),
            "user": {
                "username": purchase.user.username,
                "email": purchase.user.email,
            },
            "plan": purchase.plan.name if purchase.plan else "N/A",
            "amount": float(purchase.amount),
            "total": float(purchase.amount),
        }

        # Save to Invoice model
        Invoice.objects.create(
            user= purchase.user,
            purchase=purchase,
            invoice_number=invoice_number,
            metadata=invoice_data,
        )
        return Response(invoice_data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(
            f"Error generating invoice for purchase {purchase.pk}: {e}", exc_info=True
        )
        return Response(
            {"detail": "Invoice generation failed."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
