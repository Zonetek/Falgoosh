from api_applications.shared_models.models.scan import Scan, ScanHistory
from django.utils import timezone


class ScanRepository:
    @staticmethod
    def create_scan(user, target_ip):
        return Scan.objects.create(user=user, target_ip=target_ip, status="pending")

    @staticmethod
    def log_history(user, scan, action, details=None):
        return ScanHistory.objects.create(
            user=user, scan=scan, action=action, details=details or {}
        )

    @staticmethod
    def update_scan(scan, **fields):
        for key, value in fields.items():
            setattr(scan, key, value)
        scan.updated_at = timezone.now()
        scan.save()
        return scan
