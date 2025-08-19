from django.core.management.base import BaseCommand
from decimal import Decimal
from api_applications.shared_models.models.billing import Plan, PlanPrice

PLAN_DEFS = [
    {
        "name": "free",
        "display_name": "Free",
        "scan_limit": 100,
        "query_limit": 100,
        "duration_days": 30,
        "is_active": True,
        "prices": [{"currency": "USD", "amount": "0.00"}],
    },
    {
        "name": "member",
        "display_name": "Member",
        "scan_limit": 1000,
        "query_limit": 10000,
        "duration_days": 30,
        "is_active": True,
        "prices": [{"currency": "USD", "amount": "49.00"}],
    },
    {
        "name": "pro",
        "display_name": "Pro",
        "scan_limit": 5120,
        "query_limit": 5000,
        "duration_days": 30,
        "is_active": True,
        "prices": [{"currency": "USD", "amount": "69.00"}],
    },
    {
        "name": "premium",
        "display_name": "Premium",
        "scan_limit": 65536,
        "query_limit": 20000,
        "duration_days": 30,
        "is_active": True,
        "prices": [{"currency": "USD", "amount": "359.00"}],
    },
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