from celery import shared_task
from api_applications.shared_models.models.billing import Subscription

@shared_task
def reset_monthly_usage_task():
    Subscription.objects.update(scans_used=0, api_calls_used=0)
    return True