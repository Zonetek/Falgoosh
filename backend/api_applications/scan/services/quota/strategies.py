from api_applications.shared_models.models.billing import Subscription
from django.db.models import F
from django.utils import timezone

from .base import QuotaStrategy


class ScanQuotaStrategy(QuotaStrategy):
    def consume(self, user, count=1) -> bool:
        return (
            Subscription.objects.filter(
                user=user,
                end_date__gte=timezone.now(),
                plan__scan_limit__gte=F("scans_used") + count,
            ).update(scans_used=F("scans_used") + count)
            > 0
        )


class QueryQuotaStrategy(QuotaStrategy):
    def consume(self, user, count=1) -> bool:
        return (
            Subscription.objects.filter(
                user=user,
                end_date__gte=timezone.now(),
                plan__query_limit__gte=F("queries_used") + count,
            ).update(queries_used=F("queries_used") + count)
            > 0
        )


# Example: Report downloads, just for demo
class ReportQuotaStrategy(QuotaStrategy):
    def consume(self, user, count=1) -> bool:
        return (
            Subscription.objects.filter(
                user=user,
                end_date__gte=timezone.now(),
                plan__report_limit__gte=F("reports_used") + count,
            ).update(reports_used=F("reports_used") + count)
            > 0
        )
