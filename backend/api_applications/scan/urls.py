from django.urls import path
from .views import SearchIPView

urlpatterns = [
   path("search/", SearchIPView.as_view(), name="search_ip"),
]
