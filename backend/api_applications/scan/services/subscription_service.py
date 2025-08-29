import logging

from api_applications.shared_models.models.billing import Subscription
from django.utils import timezone

logger = logging.getLogger(__name__)


class SubscriptionService:
    @staticmethod
    def get_active_subscription(user):
        """Return active subscription or None"""
        try:
            sub = Subscription.objects.get(user=user)
            if sub.end_date >= timezone.now():
                return sub
        except Subscription.DoesNotExist:
            return None
        return None

    @staticmethod
    def activate_subscription(user, plan, duration_days):
        """Activate or extend subscription"""
        sub = Subscription.objects.filter(user=user).first()
        now = timezone.now()
        if sub and sub.end_date >= now:
            sub.end_date += timezone.timedelta(days=duration_days)
        else:
            sub = Subscription(
                user=user,
                plan=plan,
                start_date=now,
                end_date=now + timezone.timedelta(days=duration_days),
            )
        sub.save()
        return sub
