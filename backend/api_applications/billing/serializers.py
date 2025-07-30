from rest_framework import serializers
from api_applications.shared_models.models.billing import (
    SubscriptionPlan,
    PurchaseHistory,
    Invoice,
)


class CheckoutInputSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ["id", "name", "price", "description"]


class PurchaseHistorySerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = PurchaseHistory
        fields = ["id", "plan", "amount", "transaction_id", "timestamp", "success"]


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["id", "invoice_number", "metadata", "created_at"]


class FakePaymentSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
