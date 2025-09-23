import ipaddress
import logging
from django.utils import timezone

from api_applications.scan.repositories.scan_repository import ScanRepository
from api_applications.scan.services.quota.service import QuotaService
from api_applications.shared_libs.mongo_fetch_result import fetch_by_ip
from .scan_result_filter import ScanResultFilter

logger = logging.getLogger(__name__)


class ScanService:
    @staticmethod
    def validate_ip(ip):
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def initiate_scan(user, target_ip):
        if not ScanService.validate_ip(target_ip):
            return None, "Invalid IP address"

        if user and user.is_authenticated:
            if not QuotaService.consume(user, "scan", 1):
                return None, "Scan quota exhausted"
            if not QuotaService.consume(user, "query", 1):
                return None, "Query quota exhausted"
        else:
            user = None

        scan = ScanRepository.create_scan(user, target_ip)
        ScanRepository.log_history(user, scan, "created", {"ip": target_ip})
        return scan, None

    @staticmethod
    def run_scan(scan_id, target_ip):
        """
        Runs inside Celery worker — updates scan record asynchronously.
        """
        from api_applications.shared_models.models.scan import Scan

        try:
            scan = Scan.objects.get(id=scan_id)
            ScanRepository.update_scan(scan, status="running", started_at=timezone.now())
            ScanRepository.log_history(scan.user, scan, "running")

            ip_data = fetch_by_ip(target_ip)

            if ip_data:
                ScanRepository.update_scan(
                    scan,
                    status="completed",
                    completed_at=timezone.now(),
                    **{
                        k: v
                        for k, v in ip_data.items()
                        if k
                        in {
                            "country",
                            "city",
                            "region",
                            "latitude",
                            "longitude",
                            "domain",
                            "organization",
                            "isp",
                            "asn",
                        }
                    },
                )
                ScanRepository.log_history(scan.user, scan, "completed", ip_data)
            else:
                ScanRepository.update_scan(scan, status="failed")
                ScanRepository.log_history(scan.user, scan, "no_data", {"ip": target_ip})

        except Exception as e:
            logger.error(f"Run scan failed: {e}")
            from api_applications.shared_models.models.scan import Scan
            try:
                scan = Scan.objects.get(id=scan_id)
                ScanRepository.update_scan(scan, status="failed")
            except Scan.DoesNotExist:
                pass

    @staticmethod
    def get_results(user, target_ip):
        """
        Fetch results (from Mongo) and filter by user's plan.
        """
        raw_results = fetch_by_ip(target_ip) or []
        return ScanResultFilter.filter_results(user, raw_results)

    @staticmethod
    def perform_scan(user, target_ip):
        """
        Perform scan and return results in the same request.
        - If results exist, return immediately.
        - If not, create scan, fetch synchronously once, enqueue Celery for refresh.
        """
        if not ScanService.validate_ip(target_ip):
            return None, "Invalid IP address", 400

        # Try to fetch existing data
        existing_results = ScanService.get_results(user, target_ip)
        if existing_results:
            scan, _ = ScanService.initiate_scan(user, target_ip)  # ensure a scan exists
            return {
                "detail": "Scan result (cached)",
                "scan_id": scan.pk,
                "results": existing_results,
            }, None, 200

        # Create a new scan entry
        scan, error = ScanService.initiate_scan(user, target_ip)
        if not scan:
            return None, error, 403

        # Synchronous fetch (first time lookup)
        immediate_results = ScanService.get_results(user, target_ip)

        # Queue async job for updates
        from api_applications.scan.tasks import run_scan_task
        run_scan_task.delay(scan.pk, target_ip)

        return {
            "detail": "Scan queued and results fetched",
            "scan_id": scan.pk,
            "results": immediate_results,
        }, None, 202



# Special rule set for anonymous users
# ANON_RULES = {
#     "name": "anonymous",
#     "display_name": "Anonymous",
#     "description": "Anonymous users with minimal scan visibility.",
#     "scan_limit": 5,
#     "query_limit": 5,
#     "api_call_limit": 50,
#     "duration_days": None,
#     "is_active": True,
#     "os_match": False,
#     "os_family": False,
#     "accuracy": False,
#     "device_type": False,
#     "vendor": False,
#     "geo": False,
# }

