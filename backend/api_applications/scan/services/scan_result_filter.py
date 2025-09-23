from api_applications.shared_models.models.billing import Plan
import logging

logger = logging.getLogger(__name__)

class ScanResultFilter:
    """
    Filters scan results based on the user's active plan or anonymous defaults.
    """

    ANON_RULES = {
        "geo": False,
        "os_match": False,
        "os_family": False,
        "accuracy": False,
        "device_type": False,
        "vendor": False,
    }

    @staticmethod
    def get_plan_features(user) -> dict:
        """Return feature flags dict for current user (or anonymous)."""
        if not user or not user.is_authenticated:
            return ScanResultFilter.ANON_RULES

        subscription = (
            user.subscription
        )
        if subscription:
            plan = subscription.plan
        else:
            # fallback: free plan
            plan = Plan.objects.filter(
                membership=Plan.MembershipType.FREE, is_active=True
            ).first()
        
        if plan:
            return {
                "geo": plan.geo,
                "os_match": plan.os_match,
                "os_family": plan.os_family,
                "accuracy": plan.accuracy,
                "device_type": plan.device_type,
                "vendor": plan.vendor,
            } 
        return {}
    
    @staticmethod
    def filter_result(result: dict, features: dict) -> dict:
        """Apply feature flags to a single scan result."""
        if not isinstance(result, dict):
            return {"ip": str(result)}  # fallback

        filtered = {
            "last_update": result.get("last_update"),
            "ip": result.get("ip") or result.get("_id"),
            "ports": result.get("ports", []),
            "isp": result.get("general", {}).get("isp"),
            "organization": result.get("general", {}).get("organization"),
            "asn": result.get("general", {}).get("asn"),
        }

        # Geo is under result["general"]["geo"]
        if features.get("geo"):
            filtered["geo"] = result.get("general", {}).get("geo")

        # Device info comes from finger_print
        fp = result.get("finger_print", {})
        if features.get("device_type"):
            filtered["device_type"] = fp.get("type")
        if features.get("os_match"):
            filtered["os_match"] = fp.get("os_match")
        if features.get("os_family"):
            filtered["os_family"] = fp.get("os_family")
        if features.get("accuracy"):
            filtered["accuracy"] = fp.get("accuracy")
        if features.get("vendor"):
            filtered["vendor"] = fp.get("vendor")

        return filtered


    @classmethod
    def filter_results(cls, user, raw_results: list) -> list:
        features = cls.get_plan_features(user)
        if not raw_results:
            return []
        
        # If it's a dict, wrap in list
        if isinstance(raw_results, dict):
            raw_results = [raw_results]

        # If it's a string, wrap in list of dict with ip only
        if isinstance(raw_results, str):
            raw_results = [{"ip": raw_results}]

        # If it's something else (list of strings), normalize too
        normalized = []
        for r in raw_results:
            if isinstance(r, dict):
                normalized.append(r)
            elif isinstance(r, str):
                normalized.append({"ip": r})
            else:
                logger.warning(f"Unexpected scan result type: {type(r)}")

        return [cls.filter_result(r, features) for r in normalized]
        
