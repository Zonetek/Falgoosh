import logging
import uuid
from typing import Any, Dict, Optional

from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api_applications.shared_models.models.billing import Plan, PlanPrice

from .serializers import InvoiceSerializer, PlanSerializer
from .services import (
    create_invoice,
    mark_webhook_processed,
)
from .webhook_verifiers import VERIFIERS
from .webhooks import WebhookError, WebhookPayloadExtractor, WebhookProcessor

logger = logging.getLogger(__name__)


class PlanListView(generics.ListAPIView):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]


class CreateInvoiceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        currency = request.data.get("currency", "USD").upper()
        gateway = request.data.get("gateway", "bank")

        plan = get_object_or_404(Plan, pk=plan_id)
        price = PlanPrice.objects.filter(plan=plan, currency=currency).first()
        if not price:
            return Response(
                {"detail": "Price not found for currency"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice = create_invoice(
            request.user,
            plan,
            price.amount,
            currency,
            gateway,
        )
        invoice.invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"  # e.g. "001000",
        invoice.invoice_uuid = str(uuid.uuid4())

        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProviderWebhookView(APIView):

    def post(self, request: HttpRequest, provider: str) -> Response:
        """Handle webhook POST requests"""
        try:
            # Validate provider configuration
            provider_config = self._get_provider_config(provider)
            if not provider_config:
                logger.error(f"Provider {provider} not configured")
                return Response(
                    {"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Verify webhook signature
            payload = self._verify_and_parse_webhook(request, provider, provider_config)
            if payload is None:
                return Response(
                    {"error": "Invalid webhook signature or payload"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extract event ID
            provider_event_id = self._extract_event_id(
                payload, provider_config, request
            )
            if not provider_event_id:
                logger.error("Could not extract event ID from payload")
                return Response(
                    {"error": "Invalid payload format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Store raw webhook if configured
            self._store_raw_webhook(provider, provider_event_id, payload)

            # Check idempotency
            if not mark_webhook_processed(provider, provider_event_id):
                logger.info(f"Webhook {provider_event_id} already processed")
                return Response(
                    {"status": "already_processed"}, status=status.HTTP_200_OK
                )

            # Process webhook
            print("--", provider_event_id)
            processor = WebhookProcessor(provider, payload, provider_event_id)
            success = processor.process()

            if success:
                logger.info(f"Webhook {provider_event_id} processed successfully")
                return Response({"status": "success"}, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Webhook {provider_event_id} processing failed")
                return Response({"status": "failed"}, status=status.HTTP_200_OK)

        except WebhookError as e:
            logger.error(f"Webhook error: {e}")
            return Response(
                {"error": "Processing failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.exception(f"Unexpected error processing webhook: {e}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_provider_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get provider configuration from settings"""
        return getattr(settings, "PAYMENT_PROVIDERS", {}).get(provider)

    def _verify_and_parse_webhook(
        self, request: HttpRequest, provider: str, config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Verify webhook signature and parse payload"""
        verify_method = config.get("verify_method")
        verifier = VERIFIERS.get(str(verify_method))
        if not verifier:
            logger.error(f"No verifier found for method: {verify_method}")
            return None

        try:
            # Log headers for debugging
            logger.debug(f"Webhook headers for {provider}: {dict(request.headers)}")

            # Get client IP
            client_ip = self._get_client_ip(request)

            is_valid, payload = verifier(
                provider, request.body, dict(request.META), client_ip
            )

            if not is_valid:
                logger.warning(f"Invalid webhook signature for provider: {provider}")
                return None

            return payload

        except Exception as e:
            logger.error(f"Error verifying webhook for {provider}: {e}")
            return None

    def _get_client_ip(self, request: HttpRequest) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        x_real_ip = request.META.get("HTTP_X_REAL_IP")
        if x_real_ip:
            return x_real_ip

        return request.META.get("REMOTE_ADDR", "127.0.0.1")

    def _extract_event_id(
        self, payload: Dict[str, Any], config: Dict[str, Any], request: HttpRequest
    ) -> Optional[str]:

        if request and config.get("provider") == "github":
            delivery_id = request.headers.get("X-GitHub-Delivery")
            if delivery_id:
                return delivery_id

        event_id_path = config.get("event_id_path", "id")

        event_id = WebhookPayloadExtractor.extract_nested_value(payload, event_id_path)
        if event_id is None:
            event_id = payload.get("id")

        # GitHub fallback: construct from available data
        if event_id is None and payload.get("action"):
            if "issue" in payload:
                event_id = f"github_issue_{payload['issue']['id']}_{payload['action']}"
            elif "pull_request" in payload:
                event_id = (
                    f"github_pr_{payload['pull_request']['id']}_{payload['action']}"
                )
            elif "repository" in payload:
                event_id = (
                    f"github_repo_{payload['repository']['id']}_{payload['action']}"
                )

        return str(event_id) if event_id else None

    def _store_raw_webhook(
        self, provider: str, event_id: str, payload: Dict[str, Any]
    ) -> None:
        """Store raw webhook payload if configured"""
        if not getattr(settings, "STORE_RAW_WEBHOOKS", False):
            return

        try:
            from api_applications.shared_models.models.billing import RawWebhookPayload

            RawWebhookPayload.objects.create(
                provider=provider, event_id=event_id, payload=payload
            )
            logger.debug(f"Stored raw webhook payload for {provider}:{event_id}")
        except Exception as e:
            logger.warning(f"Failed to store raw webhook payload: {e}")
