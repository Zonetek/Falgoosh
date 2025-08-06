from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api_applications.tickets.views import TicketViewSet, AdminTicketViewSet

router = DefaultRouter()
router.register(r"user", TicketViewSet, basename="user-tickets")
router.register(r"admin", AdminTicketViewSet, basename="admin-tickets")

urlpatterns = [
    path("", include(router.urls)),
]