import ipaddress
import logging

from api_applications.scan.repositories.scan_repository import ScanRepository
from api_applications.scan.services.quota.service import QuotaService
from api_applications.shared_libs.mongo_fetch_result import fetch_by_ip
from billing.management.commands.seed_memberships import PLAN_DEFS
from django.utils import timezone

from api_applications.scan.services.subscription_service import (
    SubscriptionService,
)

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
        if user and user.is_authenticated:
            # Check quotas
            if not QuotaService.consume(user, "scan", 1):
                return None, "Scan quota exhausted"
            if not QuotaService.consume(user, "query", 1):
                return None, "Query quota exhausted"
        else:
            user = None

        # Create scan
        scan = ScanRepository.create_scan(user, target_ip)
        ScanRepository.log_history(user, scan, "created", {"ip": target_ip})
        return scan, None

    @staticmethod
    def run_scan(scan_id, target_ip):
        from shared_models.models.scan import (
            Scan,
        )  # local import to avoid circular deps

        try:
            scan = Scan.objects.get(id=scan_id)
            ScanRepository.update_scan(
                scan, status="running", started_at=timezone.now()
            )
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
                ScanRepository.log_history(
                    scan.user, scan, "no_data", {"ip": target_ip}
                )

        except Exception as e:
            logger.error(f"Run scan failed: {e}")
            try:
                scan = Scan.objects.get(id=scan_id)
                ScanRepository.update_scan(scan, status="failed")
            except Scan.DoesNotExist:
                pass


# Special rule set for anonymous users
ANON_RULES = {
    "name": "anonymous",
    "display_name": "Anonymous",
    "description": "Anonymous users with minimal scan visibility.",
    "scan_limit": 5,
    "query_limit": 5,
    "api_call_limit": 50,
    "duration_days": None,
    "is_active": True,
    "os_match": False,
    "os_family": False,
    "accuracy": False,
    "device_type": False,
    "vendor": False,
    "geo": False,
}


class ScanResultFilter:
    """
    Filters scan results based on user's subscription plan.
    """

    @staticmethod
    def get_plan_features(user):
        """Return feature flags for the user's active plan or anonymous rules."""
        if not user or not user.is_authenticated:
            return ANON_RULES  # anonymous → restricted

        subscription = SubscriptionService.get_active_subscription(user)
        if not subscription:
            # authenticated but no active subscription = free plan
            return next(plan for plan in PLAN_DEFS if plan["name"] == "free")

        # Find the plan definition
        for plan in PLAN_DEFS:
            if plan["name"] == subscription.plan.name:
                return plan

        # fallback to free if plan not found
        return next(plan for plan in PLAN_DEFS if plan["name"] == "free")

    @staticmethod
    def filter_result(scan_result: dict, plan: dict) -> dict:
        """Apply plan rules to a single scan result dictionary."""
        filtered = {
            "ip": scan_result.get("ip"),
            "ports": scan_result.get("ports"),
            "status": scan_result.get("status"),
        }

        if plan["geo"]:
            filtered["geo"] = scan_result.get("geo")

        if plan["device_type"]:
            filtered["device_type"] = scan_result.get("device_type")

        if plan["os_match"]:
            filtered["os_match"] = scan_result.get("os_match")

        if plan["os_family"]:
            filtered["os_family"] = scan_result.get("os_family")

        if plan["accuracy"]:
            filtered["accuracy"] = scan_result.get("accuracy")

        if plan["vendor"]:
            filtered["vendor"] = scan_result.get("vendor")

        return filtered

    @classmethod
    def filter_results(cls, user, scan_results: list) -> list:
        """Filter a list of scan results according to plan rules."""
        plan = cls.get_plan_features(user)
        return [cls.filter_result(result, plan) for result in scan_results]
