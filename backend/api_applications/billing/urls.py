from django.urls import path
from .payments import FakePaymentView
from .views import (
    PlanListView,
    CreateCheckoutView,
    InvoiceListView,
    InvoiceDetailView,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plan-list"),
    path("checkout/", CreateCheckoutView.as_view(), name="checkout"),
    path('fake-payment/', FakePaymentView.as_view(), name='fake-payment'),
    path("invoices/", InvoiceListView.as_view(), name="invoice-list"),
    path(
        "invoices/<int:pk>/",
        InvoiceDetailView.as_view(),
        name="invoice-detail",
    ),
]
