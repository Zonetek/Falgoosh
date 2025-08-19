from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Plan(models.Model):
    """Catalog of available plans (definitions only)."""

    class MembershipType(models.TextChoices):
        FREE = "free", _("Free")
        MEMBER = "member", _("Member")
        PRO = "pro", _("Pro")
        PREMIUM = "premium", _("Premium")

    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    # features
    os_match = models.BooleanField(default=False)
    os_family = models.BooleanField(default=False)
    accuracy = models.BooleanField(default=False)
    device_type = models.BooleanField(default=False)
    vendor = models.BooleanField(default=False)
    geo = models.BooleanField(default=False)
    scan_limit = models.PositiveIntegerField(default=0)  # scans per billing period
    query_limit = models.PositiveIntegerField(default=0)  # queries per billing period
    api_call_limit = models.PositiveIntegerField(default=1000)  # monthly API calls
    monitored_ips = models.PositiveIntegerField(default=0)
    membership = models.CharField(
        max_length=20,
        choices=MembershipType,
        default=MembershipType.FREE,
    )

    # plan length in days (e.g. 30 for monthly)
    duration_days = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Plans"

    def __str__(self):
        return self.display_name or self.name


class PlanPrice(models.Model):
    """Stores multi-currency prices for each plan."""

    plan = models.ForeignKey(Plan, related_name="prices", on_delete=models.CASCADE)
    currency = models.CharField(max_length=3)  # e.g., USD, EUR, IRR
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )

    class Meta:
        unique_together = ("plan", "currency")

    def __str__(self):
        return f"{self.plan.name} - {self.currency} {self.amount}"


class Subscription(models.Model):
    """A user subscription (what the user actually has)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)

    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    canceled_at = models.DateTimeField(null=True, blank=True)

    # usage counters for the current billing period
    scans_used = models.PositiveIntegerField(default=0)
    queries_used = models.PositiveIntegerField(default=0)
    api_calls_used = models.PositiveIntegerField(default=0)

    # store external subscription id from provider (bank/psp)
    external_subscription_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"

    def __str__(self):
        return f"{self.user} -> {self.plan.name} ({self.start_date.date()} - {self.end_date.date()})"

    def is_active(self):
        return self.end_date >= timezone.now()

    def remaining_scans(self):
        if not self.plan:
            return 0
        return max(0, self.plan.scan_limit - self.scans_used)

    def remaining_queries(self):
        return max(0, self.plan.query_limit - self.queries_used)

    def remaining_api_calls(self):
        if not self.plan:
            return 0
        return max(0, self.plan.api_call_limit - self.api_calls_used)

    def consume_scans(self, count: int = 1):
        if self.remaining_scans() < count:
            return False
        self.scans_used = models.F("scans_used") + count
        self.save(update_fields=["scans_used"])
        self.refresh_from_db(fields=["scans_used"])
        return True

    def consume_queries(self, count: int = 1):
        if self.remaining_queries() < count:
            return False
        self.queries_used = models.F("queries_used") + count
        self.save(update_fields=["queries_used"])
        self.refresh_from_db(fields=["queries_used"])
        return True

    def reset_usage(self):
        self.scans_used = 0
        self.queries_used = 0
        self.save(update_fields=["scans_used", "queries_used"])


class Invoice(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    invoice_uuid = models.UUIDField(null=True, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    invoice_number = models.CharField(
        max_length=50, unique=True, null=True, editable=False
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    payment_gateway = models.CharField(max_length=50, blank=True, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    def mark_as_paid(self, transaction_id=None):
        self.status = "paid"
        self.paid_at = timezone.now()
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()

    def __str__(self) -> str:
        return f"Invoice {self.invoice_number} — {self.user.email}"


class PurchaseHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    plan_name = models.CharField(max_length=100)
    plan_id = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    payment_status = models.CharField(
        max_length=20, choices=Invoice.STATUS_CHOICES, default="pending"
    )
    purchased_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    invoice = models.OneToOneField(
        Invoice, on_delete=models.SET_NULL, blank=True, null=True
    )


class WebhookEvent(models.Model):
    """
    Record Stripe webhook event ids we've processed for idempotency.
    """

    provider = models.CharField(max_length=32)  # 'stripe'
    event_id = models.CharField(max_length=128, unique=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["provider", "event_id"])]

    def __str__(self):
        return f"{self.provider}:{self.event_id}"


class RawWebhookPayload(models.Model):
    """
    store raw payloads for debugging/audit. Consider GDPR/PII implications before enabling in production.
    """

    provider = models.CharField(max_length=32)
    event_id = models.CharField(max_length=128, null=True, blank=True)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["provider", "event_id"])]
