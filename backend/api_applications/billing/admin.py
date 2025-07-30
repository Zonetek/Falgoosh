from django.contrib import admin
from api_applications.shared_models.models.billing import (
    SubscriptionPlan,
    PurchaseHistory,
    Invoice,
)

admin.site.register(SubscriptionPlan)
admin.site.register(PurchaseHistory)
admin.site.register(Invoice)
