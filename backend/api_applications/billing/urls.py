from django.urls import path
from .views import (
    PlanListView,
    CreateInvoiceView,
    ProviderWebhookView,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plans-list"),
    path("invoices/create/", CreateInvoiceView.as_view(), name="invoice-create"),
    path(
        "webhook/<str:provider>/",
        ProviderWebhookView.as_view(),
        name="provider-webhook",
    ),

]
