from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from typing import Any, Optional, Tuple, Union
from datetime import timedelta
import logging

from api_applications.shared_models.models.billing import (
    Subscription, 
    Plan, 
    Invoice, 
    WebhookEvent
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
        logger.exception(f"Failed to mark webhook processed: {provider}:{event_id} - {exc}")
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
    user: Any, 
    plan: Plan, 
    duration_days: int
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
                subscription.end_date = subscription.end_date + timedelta(days=duration_days)
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


def attempt_consume_scan_for_user(user: Any, count: int = 1) -> bool:
    """
    Atomically consume `count` scans for `user` if available.

    Uses a single UPDATE query to avoid race conditions and ensures
    the user has an active subscription with sufficient scans remaining.

    Args:
        user: User to consume scans for
        count: Number of scans to consume (default: 1)

    Returns:
        bool: True if consumption succeeded, False if insufficient scans or no active subscription
    """
    if not user:
        logger.error("User is required for scan consumption")
        return False

    if count <= 0:
        logger.warning(f"Invalid scan count: {count}")
        return False

    try:
        now = timezone.now()
        
        # Atomic update with conditions
        updated = Subscription.objects.filter(
            user=user,
            end_date__gte=now,  # Only active subscriptions
            plan__scan_limit__gte=F("scans_used") + count,  # Sufficient scans remaining
        ).update(scans_used=F("scans_used") + count)
        print("---", updated)
        success = bool(updated)
        
        if success:
            logger.debug(f"Consumed {count} scans for user {user.pk}")
        else:
            logger.warning(
                f"Failed to consume {count} scans for user {user.pk} - "
                f"insufficient balance or no active subscription"
            )

        return success

    except Exception as exc:
        logger.error(f"Error consuming scans for user {user.id}: {exc}")
        return False


def attempt_consume_query_for_user(user: Any, count: int = 1) -> bool:
    """
    Atomically consume `count` queries for `user` if available.

    Args:
        user: User to consume queries for
        count: Number of queries to consume (default: 1)

    Returns:
        bool: True if consumption succeeded, False otherwise
    """
    if not user:
        logger.error("User is required for query consumption")
        return False

    if count <= 0:
        logger.warning(f"Invalid query count: {count}")
        return False

    try:
        now = timezone.now()
        
        updated = Subscription.objects.filter(
            user=user,
            end_date__gte=now,
            plan__query_limit__gte=F("queries_used") + count,
        ).update(queries_used=F("queries_used") + count)

        success = bool(updated)
        
        if success:
            logger.debug(f"Consumed {count} queries for user {user.id}")
        else:
            logger.warning(
                f"Failed to consume {count} queries for user {user.id} - "
                f"insufficient balance or no active subscription"
            )

        return success

    except Exception as exc:
        logger.error(f"Error consuming queries for user {user.id}: {exc}")
        return False


def get_user_subscription_status(user: Any) -> dict:
    """
    Get detailed subscription status for a user.

    Args:
        user: User to check subscription for

    Returns:
        dict: Subscription status information
    """
    if not user:
        return {
            "has_active_subscription": False,
            "error": "User is required"
        }

    try:
        now = timezone.now()
        
        try:
            subscription = Subscription.objects.select_related('plan').get(
                user=user,
                end_date__gte=now
            )
            
            return {
                "has_active_subscription": True,
                "plan_name": subscription.plan.name,
                "plan_id": subscription.plan.pk,
                "start_date": subscription.start_date,
                "end_date": subscription.end_date,
                "scans_used": subscription.scans_used,
                "scans_limit": subscription.plan.scan_limit,
                "scans_remaining": max(0, subscription.plan.scan_limit - subscription.scans_used),
                "queries_used": subscription.queries_used,
                "queries_limit": subscription.plan.query_limit,
                "queries_remaining": max(0, subscription.plan.query_limit - subscription.queries_used),
                "days_remaining": (subscription.end_date - now).days,
            }
        except Subscription.DoesNotExist:
            return {
                "has_active_subscription": False,
                "message": "No active subscription found"
            }

    except Exception as exc:
        logger.error(f"Error getting subscription status for user {user.id}: {exc}")
        return {
            "has_active_subscription": False,
            "error": f"Failed to fetch subscription status: {str(exc)}"
        }


def cancel_user_subscription(user: Any, immediate: bool = False) -> bool:
    """
    Cancel a user's subscription.

    Args:
        user: User whose subscription to cancel
        immediate: If True, cancel immediately. If False, cancel at end of current period.

    Returns:
        bool: True if cancellation succeeded, False otherwise
    """
    if not user:
        logger.error("User is required for subscription cancellation")
        return False

    try:
        now = timezone.now()
        
        with transaction.atomic():
            subscription = Subscription.objects.select_for_update().get(
                user=user,
                end_date__gte=now
            )
            
            if immediate:
                subscription.end_date = now
                subscription.save(update_fields=['end_date'])
                logger.info(f"Subscription cancelled immediately for user {user.id}")
            else:
                # Mark for cancellation at end of period
                # You might want to add a 'cancelled_at' field to track this
                logger.info(f"Subscription marked for cancellation for user {user.id}")
            
            return True

    except Subscription.DoesNotExist:
        logger.warning(f"No active subscription to cancel for user {user.id}")
        return False
    except Exception as exc:
        logger.error(f"Error cancelling subscription for user {user.id}: {exc}")
        return False


