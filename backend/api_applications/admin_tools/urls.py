from rest_framework.routers import DefaultRouter
from api_applications.admin_tools.views import AdminUserViewSet, AdminScanViewSet

router = DefaultRouter()
router.register(r'users', AdminUserViewSet, basename='admin-user')
router.register(r'scans', AdminScanViewSet, basename='admin-scan')

urlpatterns = router.urls