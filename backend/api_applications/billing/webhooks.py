import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.db import transaction

from api_applications.shared_models.models.billing import Plan

from .services import activate_or_extend_subscription, create_invoice

logger = logging.getLogger(__name__)
base_user = get_user_model()


class WebhookError(Exception):
    """Custom exception for webhook processing errors"""

    pass


class WebhookPayloadExtractor:
    """Helper class for extracting data from webhook payloads"""

    @staticmethod
    def extract_nested_value(payload: dict, path: str) -> Optional[Any]:
        """
        Extract nested value from payload using dot notation path
        Example: extract_nested_value(payload, "data.object.id")
        """
        if not path or not isinstance(payload, dict):
            return None

        parts = path.split(".")
        current = payload

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @staticmethod
    def extract_user_id(payload: dict, metadata: dict) -> Optional[int]:
        """Extract and validate user_id from payload or metadata"""
        user_id = metadata.get("user_id") or payload.get("user_id")

        if user_id is None:
            return None

        try:
            return int(user_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id format: {user_id}")
            return None

    @staticmethod
    def extract_plan_id(payload: dict, metadata: dict) -> Optional[str]:
        """Extract plan_id from payload or metadata"""
        return metadata.get("plan_id") or payload.get("plan_id")

    @staticmethod
    def extract_amount(payload: dict) -> Optional[Decimal]:
        """Extract and normalize amount from payload"""
        amount = payload.get("amount")

        if amount is None:
            return None

        try:
            # Convert to Decimal for precise money calculations
            if isinstance(amount, int):
                # Assuming amount is in cents (common for Stripe, etc.)
                return Decimal(amount) / Decimal("100")
            elif isinstance(amount, (float, str)):
                return Decimal(str(amount))
            else:
                return Decimal(amount)
        except (InvalidOperation, TypeError, ValueError) as e:
            logger.warning(f"Invalid amount format: {amount}, error: {e}")
            return None

    @staticmethod
    def extract_currency(payload: dict) -> str:
        """Extract currency from payload with fallback to USD"""
        return (
            payload.get("currency")
            or payload.get("curr")
            or payload.get("currency_code")
            or "USD"
        ).upper()


class WebhookProcessor:
    """Main webhook processing logic"""

    def __init__(self, provider: str, payload: dict, provider_event_id: str):
        self.provider = provider
        self.payload = payload
        self.provider_event_id = provider_event_id
        self.extractor = WebhookPayloadExtractor()
    def process(self) -> bool:
        """
        Process the webhook payload
        Returns True if processing was successful, False otherwise
        """
        try:
            with transaction.atomic():
                return self._process_payment()
        except Exception as e:
            logger.exception(
                f"Error processing webhook for provider {self.provider}: {e}"
            )
            raise WebhookError(f"Processing failed: {str(e)}")

    def _process_payment(self) -> bool:
        """Process payment-related webhook"""
        metadata = self.payload.get("metadata", {}) or {}

        # Extract required data
        user_id = (
        self.extractor.extract_user_id(self.payload, metadata)
        or self.extractor.extract_nested_value(self.payload, "data.object.metadata.user_id")
        )
        plan_id = self.extractor.extract_plan_id(self.payload, metadata)
        amount = self.extractor.extract_amount(self.payload)
        currency = self.extractor.extract_currency(self.payload)
        
        # Validate required fields
        if not all([user_id, plan_id, amount]):
            logger.warning(
                f"Missing required fields - user_id: {user_id}, "
                f"plan_id: {plan_id}, amount: {amount}"
            )
            return False

        # Get user and plan objects
        user = self._get_user(user_id)
        plan = self._get_plan(plan_id)

        if not user or not plan:
            logger.warning(f"User or plan not found - user: {user}, plan: {plan}")
            return False

        # Create invoice and activate subscription
        return self._create_invoice_and_activate(user, plan, amount, currency)

    def _get_user(self, user_id: int):
        """Get user by ID with error handling"""
        try:
            return base_user.objects.get(pk=user_id)
        except base_user.DoesNotExist:
            logger.error(f"User with ID {user_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None

    def _get_plan(self, plan_id: str) -> Optional[Plan]:
        """Get plan by ID with error handling"""
        try:
            return Plan.objects.get(pk=plan_id)
        except Plan.DoesNotExist:
            logger.error(f"Plan with ID {plan_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching plan {plan_id}: {e}")
            return None

    def _create_invoice_and_activate(
        self, user: Any, plan: Plan, amount: Decimal, currency: str
    ) -> bool:
        """Create invoice and activate subscription"""
        try:
            # Create invoice
            invoice = create_invoice(
                user=user,
                plan=plan,
                amount=amount,
                currency=currency,
                gateway=self.provider,
                transaction_id=self.provider_event_id,
            )

            # Mark invoice as paid
            invoice.mark_as_paid(transaction_id=self.provider_event_id)
            invoice.save(update_fields=["status", "paid_at"])

            # Activate or extend subscription
            activate_or_extend_subscription(user, plan, plan.duration_days)

            logger.info(
                f"Successfully processed payment - User: {user.id}, "
                f"Plan: {plan.pk}, Amount: {amount} {currency}, "
                f"Invoice: {invoice.pk}"
            )

            return True

        except Exception as e:
            logger.error(
                f"Error creating invoice or activating subscription: {e} - "
                f"User: {user.id}, Plan: {plan.pk}, Amount: {amount}"
            )
            return False
