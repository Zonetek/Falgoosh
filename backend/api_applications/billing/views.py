from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api_applications.shared_models.models.billing import SubscriptionPlan, Invoice
from .serializers import CheckoutInputSerializer, SubscriptionPlanSerializer, InvoiceSerializer
from .payments import create_checkout_session
from typing import Any
from django.db.models.query import QuerySet

import logging

logger = logging.getLogger(__name__)


class PlanListView(generics.ListAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer


class CreateCheckoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CheckoutInputSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Checkout input validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        plan_id = serializer.validated_data["plan_id"]

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            logger.warning(f"Checkout failed: SubscriptionPlan with id={plan_id} not found.")
            return Response(
                {"detail": "Subscription plan not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            session = create_checkout_session(request.user, plan)
            logger.info(f"Checkout session created for user {request.user.id} with plan {plan.name}")
            return Response({"checkout_url": session.url}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}", exc_info=True)
            return Response(
                {"detail": "Checkout session creation failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InvoiceListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self) -> QuerySet[Any]:
        try:
            return Invoice.objects.filter(user=self.request.user)
        except Exception as e:
            logger.error(
                f"Failed to retrieve invoices for user {self.request.user}: {e}"
            )
            return Invoice.objects.none()


class InvoiceDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self) -> QuerySet[Any]:
        try:
            return Invoice.objects.filter(user=self.request.user)
        except Exception as e:
            logger.error(
                f"Failed to retrieve invoices for user {self.request.user}: {e}"
            )
