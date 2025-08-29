from rest_framework import serializers

from api_applications.shared_models.models.billing import (
    Invoice,
    Plan,
    PlanPrice,
    PurchaseHistory,
    Subscription,
)


class PlanPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanPrice
        fields = ["currency", "amount"]


class PlanSerializer(serializers.ModelSerializer):
    prices = PlanPriceSerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "display_name",
            "description",
            "scan_limit",
            "query_limit",
            "os_match",
            "os_family",
            "accuracy",
            "device_type",
            "vendor",
            "geo",
            "monitored_ips",
            "membership",
            "duration_days",
            "prices",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ["plan", "start_date", "end_date", "scans_used", "queries_used"]


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            "invoice_uuid",
            "user",
            "invoice_number",
            "plan",
            "amount",
            "currency",
            "status",
            "payment_gateway",
            "issued_at",
            "transaction_id",
            "created_at",
            "paid_at",
        ]


class PurchaseHistorySerializer(serializers.ModelSerializer):
    plan = SubscriptionSerializer(read_only=True)

    class Meta:
        model = PurchaseHistory
        fields = [
            "user",
            "plan_name",
            "plan_id",
            "price",
            "currency",
            "payment_status",
            "purchased_at",
            "expires_at",
            "invoice",
        ]
