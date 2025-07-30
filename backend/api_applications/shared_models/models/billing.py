from django.conf import settings
from django.db import models
from django.utils import timezone


def upload_invoice_path(instance, filename):
    return f"invoices/user_{instance.invoice.user.id}/{filename}"


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stripe_plan_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class PurchaseHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases"
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    timestamp = models.DateTimeField(default=timezone.now)
    success = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.plan} at {self.timestamp}"


class Invoice(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoices"
    )
    purchase = models.OneToOneField(
        PurchaseHistory, on_delete=models.CASCADE, related_name="invoice"
    )
    invoice_number = models.CharField(max_length=20, unique=True)
    metadata = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} for {self.user.username}"
