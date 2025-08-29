import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any, Optional, Tuple, Union

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from api_applications.shared_models.models.billing import (
    Invoice,
    Plan,
    Subscription,
    WebhookEvent,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class BillingServiceError(Exception):
    """Base exception for billing service errors"""

    pass


class InvoiceCreationError(BillingServiceError):
    """Exception raised when invoice creation fails"""

    pass


class SubscriptionError(BillingServiceError):
    """Exception raised when subscription operations fail"""

    pass


def mark_webhook_processed(provider: str, event_id: str) -> bool:
    """
    Record a processed webhook event idempotently.

    Args:
        provider: Payment provider name (e.g., 'stripe', 'paypal')
        event_id: Unique event identifier from the provider

    Returns:
        bool: True when the event was recorded (first time), False if it already existed.

    Raises:
        Exception: On unexpected database errors (not IntegrityError)
    """
    if not provider or not event_id:
        logger.error(f"Invalid parameters - provider: {provider}, event_id: {event_id}")
        raise ValueError("Provider and event_id cannot be empty")

    try:
        WebhookEvent.objects.create(provider=provider, event_id=event_id)
        logger.info(f"Webhook event recorded: {provider}:{event_id}")
        return True
    except IntegrityError:
        # Already processed (unique constraint violation)
        logger.debug(f"Webhook event already processed: {provider}:{event_id}")
        return False
    except Exception as exc:
        logger.exception(
            f"Failed to mark webhook processed: {provider}:{event_id} - {exc}"
        )
        raise


@transaction.atomic
def create_invoice(
    user: Any,
    plan: Plan,
    amount: Union[Decimal, float, int],
    currency: str,
    gateway: str,
    transaction_id: Optional[str] = None,
    description: Optional[str] = None,
) -> Invoice:
    """
    Create an invoice for a user's plan purchase.

    Args:
        user: User making the purchase
        plan: Plan being purchased
        amount: Amount to charge (will be converted to Decimal)
        currency: Currency code (e.g., 'USD', 'EUR')
        gateway: Payment gateway name
        transaction_id: Optional transaction ID from payment provider
        description: Optional invoice description

    Returns:
        Invoice: Created invoice instance

    Raises:
        InvoiceCreationError: If invoice creation fails
        ValueError: If parameters are invalid
    """
    if not all([user, plan, gateway]):
        raise ValueError("User, plan, and gateway are required")

    if not currency or len(currency) != 3:
        raise ValueError("Currency must be a valid 3-letter code")

    try:
        # Ensure amount is a Decimal for precise money handling
        decimal_amount = Decimal(str(amount))

        if decimal_amount <= 0:
            raise ValueError("Amount must be positive")

        # Generate description if not provided
        if not description:
            description = f"Payment for {plan.name} plan"

        invoice = Invoice.objects.create(
            user=user,
            plan=plan,
            currency=currency.upper(),
            amount=decimal_amount,
            payment_gateway=gateway.lower(),
            transaction_id=transaction_id,
        )

        logger.info(
            f"Invoice created - ID: {invoice.pk}, User: {user.pk}, "
            f"Plan: {plan.pk}, Amount: {decimal_amount} {currency}"
        )

        return invoice

    except Exception as exc:
        logger.error(
            f"Failed to create invoice - User: {user.id}, Plan: {plan.pk}, "
            f"Amount: {amount}, Error: {exc}"
        )
        raise InvoiceCreationError(f"Invoice creation failed: {str(exc)}")


@transaction.atomic
def activate_or_extend_subscription(
    user: Any, plan: Plan, duration_days: int
) -> Tuple[Subscription, bool]:
    """
    Activate a new subscription or extend an existing one.

    Args:
        user: User to activate/extend subscription for
        plan: Plan to subscribe to
        duration_days: Duration of the subscription in days

    Returns:
        Tuple[Subscription, bool]: (subscription_instance, was_created)

    Raises:
        SubscriptionError: If subscription operation fails
        ValueError: If parameters are invalid
    """
    if not all([user, plan]):
        raise ValueError("User and plan are required")

    if duration_days <= 0:
        raise ValueError("Duration must be positive")

    try:
        now = timezone.now()

        # Use select_for_update to prevent race conditions
        subscription, created = Subscription.objects.select_for_update().get_or_create(
            user=user,
            defaults={
                "plan": plan,
                "start_date": now,
                "end_date": now + timedelta(days=duration_days),
                "scans_used": 0,
                "queries_used": 0,
            },
        )

        if created:
            logger.info(
                f"New subscription created - User: {user.id}, Plan: {plan.pk}, "
                f"Duration: {duration_days} days"
            )
        else:
            # Extend existing subscription
            old_end_date = subscription.end_date

            if subscription.end_date < now:
                # Subscription expired, reset it
                subscription.start_date = now
                subscription.end_date = now + timedelta(days=duration_days)
                subscription.scans_used = 0
                subscription.queries_used = 0
                logger.info(f"Expired subscription reset - User: {user.id}")
            else:
                # Active subscription, extend it
                subscription.end_date = subscription.end_date + timedelta(
                    days=duration_days
                )
                logger.info(
                    f"Active subscription extended - User: {user.id}, "
                    f"From: {old_end_date}, To: {subscription.end_date}"
                )

            # Update plan in case it changed
            subscription.plan = plan
            subscription.save(
                update_fields=[
                    "start_date",
                    "end_date",
                    "plan",
                    "scans_used",
                    "queries_used",
                ]
            )

        return subscription, created

    except Exception as exc:
        logger.error(
            f"Failed to activate/extend subscription - User: {user.id}, "
            f"Plan: {plan.pk}, Error: {exc}"
        )
        raise SubscriptionError(f"Subscription operation failed: {str(exc)}")
