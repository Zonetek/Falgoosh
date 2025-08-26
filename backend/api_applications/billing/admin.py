from django.contrib import admin

from api_applications.shared_models.models.billing import (
    Plan,
    PlanPrice,
    Subscription,
    Invoice,
    WebhookEvent,
    RawWebhookPayload,
)


class PlanPriceInline(admin.TabularInline):
    model = PlanPrice
    extra = 1


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "display_name",
        "scan_limit",
        "query_limit",
        "duration_days",
        "is_active",
    )
    inlines = [PlanPriceInline]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "start_date",
        "end_date",
        "scans_used",
        "queries_used",
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "invoice_uuid",
        "user",
        "plan",
        "amount",
        "currency",
        "status",
        "transaction_id",
        "created_at",
        "issued_at",
    )


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_id", "processed_at")


@admin.register(RawWebhookPayload)
class RawWebhookPayloadAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_id", "created_at")
