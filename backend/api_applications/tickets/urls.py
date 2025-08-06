from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserTicketViewSet, AdminTicketViewSet

router = DefaultRouter()
router.register(r"user/", UserTicketViewSet, basename="user-tickets")
router.register(r"admin/", AdminTicketViewSet, basename="admin-tickets")

urlpatterns = [
    path("", include(router.urls)),
]