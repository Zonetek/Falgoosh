from celery import shared_task
from api_applications.shared_models.models.user import UserProfile

@shared_task
def reset_monthly_usage_task():
    UserProfile.objects.update(scans_used=0, api_calls_used=0)
    return True