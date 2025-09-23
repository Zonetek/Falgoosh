import logging
import os

from django.core.cache import cache
from dotenv import load_dotenv
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api_applications.scan.serializers import ScanHistorySerializer, ScanSerializer
from api_applications.shared_models.models.scan import Scan, ScanHistory

from .services.scan_service import  ScanService

load_dotenv()

logger = logging.getLogger(__name__)

ANON_SCAN_LIMIT = int(os.getenv("ANON_SCAN_LIMIT", 10))
ANON_SCAN_WINDOW = int(os.getenv("ANON_SCAN_WINDOW", 86400))


class PerformScanView(APIView):
    """
    User searches IP → get results immediately (cached or fetched).
    Still enqueues Celery for background refresh.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ip = request.GET.get("ip")
        user = request.user if request.user.is_authenticated else None

        # Anonymous quota check
        if not user:
            client_ip = request.META.get("REMOTE_ADDR", "unknown")
            cache_key = f"anon_scan_count:{client_ip}"
            count = cache.get(cache_key, 0)
            if count >= ANON_SCAN_LIMIT:
                return Response(
                    {"detail": "Anonymous scan limit reached. Please register."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            cache.set(cache_key, count + 1, timeout=ANON_SCAN_WINDOW)

        payload, error, code = ScanService.perform_scan(user, ip)
        if not payload:
            return Response({"detail": error}, status=code)

        return Response(payload, status=code)


class UserScansView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        scans = Scan.objects.filter(user=request.user).order_by("-created_at")
        serializer = ScanSerializer(scans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserScanHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, scan_id):
        try:
            scan = Scan.objects.get(pk=scan_id, user=request.user)
        except Scan.DoesNotExist:
            return Response(
                {"error": "Scan not found."}, status=status.HTTP_404_NOT_FOUND
            )

        history_qs = ScanHistory.objects.filter(scan=scan).order_by("-timestamp")
        serializer = ScanHistorySerializer(history_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
