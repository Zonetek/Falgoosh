from django.core.management.base import BaseCommand
from decimal import Decimal
from api_applications.shared_models.models.billing import Plan, PlanPrice

PLAN_DEFS = [
  {
    "name": "free",
    "display_name": "Free",
    "description": "Free plan with limited scans and queries for testing.",
    "scan_limit": 100,
    "query_limit": 100,
    "api_call_limit": 1000,
    "duration_days": 30,
    "is_active": True,
    "prices": [{ "currency": "USD", "amount": "0.00" }],
    "os_match": False,
    "os_family": False,
    "accuracy": False,
    "device_type": True,
    "vendor": False,
    "geo": True
  },
  {
    "name": "member",
    "display_name": "Member",
    "description": "Entry-level paid plan with higher limits and improved accuracy.",
    "scan_limit": 1000,
    "query_limit": 2000,
    "api_call_limit": 5000,
    "duration_days": 30,
    "is_active": True,
    "prices": [{ "currency": "USD", "amount": "9.99" }],
    "os_match": True,
    "os_family": True,
    "accuracy": False,
    "device_type": True,
    "vendor": False,
    "geo": True
  },
  {
    "name": "pro",
    "display_name": "Pro",
    "description": "Professional plan with larger scan limits, advanced accuracy, and priority scanning.",
    "scan_limit": 10000,
    "query_limit": 20000,
    "api_call_limit": 50000,
    "duration_days": 30,
    "is_active": True,
    "prices": [{ "currency": "USD", "amount": "49.99" }],
    "os_match": True,
    "os_family": True,
    "accuracy": False,
    "device_type": True,
    "vendor": True,
    "geo": True
  },
  {
    "name": "premium",
    "display_name": "Premium",
    "description": "Top-tier plan with maximum limits, enterprise-grade accuracy, and full feature set.",
    "scan_limit": 100000,
    "query_limit": 200000,
    "api_call_limit": 1000000,
    "duration_days": 30,
    "is_active": True,
    "prices": [{ "currency": "USD", "amount": "199.99" }],
    "os_match": True,
    "os_family": True,
    "accuracy": "premium",
    "device_type": True,
    "vendor": True,
    "geo": True
  }
]


class Command(BaseCommand):
    help = "Seed or update default plans and their prices."

    def handle(self, *args, **options):
        for p in PLAN_DEFS:
            plan, created = Plan.objects.update_or_create(
                name=p["name"],
                defaults={
                    "display_name": p["display_name"],
                    "scan_limit": p["scan_limit"],
                    "query_limit": p["query_limit"],
                    "duration_days": p["duration_days"],
                    "is_active": p.get("is_active", True),
                },
            )
            # prices (multi-currency)
            for price in p.get("prices", []):
                PlanPrice.objects.update_or_create(
                    plan=plan,
                    currency=price["currency"].upper(),
                    defaults={"amount": Decimal(price["amount"])},
                )

            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} plan: {plan.name} (id={plan.pk})")

        self.stdout.write(self.style.SUCCESS("Plan seeding complete."))