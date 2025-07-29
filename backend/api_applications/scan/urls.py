from django.urls import path
from .views import SearchIPView, UserScansView, UserScanHistoryView

urlpatterns = [
   path("search/", SearchIPView.as_view(), name="search_ip"),
   path('scans/', UserScansView.as_view(), name='user_scans'),
    path('scans/<int:scan_id>/history/', UserScanHistoryView.as_view(), name='user_scan_history'),
]
