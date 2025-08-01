import logging
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from api_applications.shared_models.models.billing import (
    SubscriptionPlan,
    PurchaseHistory,
)
from .invoices import generate_invoice
import random
from .serializers import FakePaymentSerializer
import uuid

logger = logging.getLogger(__name__)


class FakePaymentView(generics.GenericAPIView):
    """Handle fake payment processing."""
    permission_classes = [IsAuthenticated]
    serializer_class = FakePaymentSerializer

    def post(self, request, *args, **kwargs):
        plan_id = request.data.get("plan_id")
        if not plan_id:
            return Response(
                {"detail": "plan_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            logger.warning(f"FakePayment: Invalid plan_id={plan_id}")
            return Response(
                {"detail": "Subscription plan not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            transaction_id = f"FAKE-{uuid.uuid4().hex[:12].upper()}"
            user = request.user

            purchase = PurchaseHistory.objects.create(
                user=user, plan=plan, amount=plan.price, transaction_id=transaction_id
            )

            user.userprofile.membership = plan.name.lower()
            user.userprofile.save()
            random_number = random.randint(1000, 9999)
            generate_invoice(purchase, f"INV-{random_number}")

            return Response(
                {
                    "message": "Fake payment processed successfully.",
                    "invoice_number": f"INV-{random_number}",
                    "transaction_id": transaction_id,
                    "amount": str(plan.price),
                    "plan": plan.name,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"FakePayment error: {e}", exc_info=True)
            return Response(
                {"detail": "Fake payment failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DummySession:
    def __init__(self, url):
        self.url = url


def create_checkout_session(user, plan):
    # In production, integrate with Stripe or another gateway here
    fake_url = f"https://example.com/checkout?user={user.id}&plan={plan.id}"
    return DummySession(url=fake_url)
