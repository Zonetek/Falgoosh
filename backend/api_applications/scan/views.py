import logging
import os

from django.core.cache import cache
from dotenv import load_dotenv
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api_applications.scan.serializers import ScanHistorySerializer, ScanSerializer
from api_applications.scan.services.subscription_service import SubscriptionService
from api_applications.shared_models.models.scan import Scan, ScanHistory

from .services.scan_service import ScanResultFilter, ScanService
from .tasks import run_scan_task

load_dotenv()

logger = logging.getLogger(__name__)

ANON_SCAN_LIMIT = int(os.getenv("ANON_SCAN_LIMIT", 10))
ANON_SCAN_WINDOW = int(os.getenv("ANON_SCAN_WINDOW", 86400))


class PerformScanView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        target_ip = request.GET.get("ip")

        if not target_ip or not ScanService.validate_ip(target_ip):
            return Response(
                {"detail": "Invalid IP address"}, status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.is_authenticated:
            subscription = SubscriptionService.get_active_subscription(request.user)
            if not subscription:
                return Response({"detail": "No active subscription"}, status=403)

            scan, error = ScanService.initiate_scan(request.user, target_ip)
            if not scan:
                return Response({"detail": error}, status=status.HTTP_403_FORBIDDEN)

            run_scan_task.delay(scan.pk, target_ip)

            # fetch results (if any already exist, otherwise empty list)
            # raw_results = ScanService.get_results(scan.pk)
            # filtered_results = ScanResultFilter.filter_results(
                # request.user, raw_results
            # )
            return Response(
                {
                    "detail": "Scan queued",
                    "scan_id": scan.pk,
                    # "results": filtered_results,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        # Handle anonymous user (quota based on IP)
        client_ip = request.META.get("REMOTE_ADDR", "unknown")
        cache_key = f"anon_scan_count:{client_ip}"
        count = cache.get(cache_key, 0)

        if count >= ANON_SCAN_LIMIT:
            return Response(
                {
                    "detail": "Anonymous scan limit reached. Please register for more scans."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        cache.set(cache_key, count + 1, timeout=ANON_SCAN_WINDOW)

        # Anonymous scan (user=None in DB)
        scan, error = ScanService.initiate_scan(None, target_ip)
        if not scan:
            return Response(
                {"detail": error},
                status=status.HTTP_403_FORBIDDEN,
            )

        run_scan_task.delay(scan.pk, target_ip)

        # fetch results for anonymous (limited visibility)
        # raw_results = ScanService.run_scan(scan.pk)
        # filtered_results = ScanResultFilter.filter_results(None, raw_results)

        return Response(
            {
                "detail": "Anonymous scan queued",
                "scan_id": scan.pk,
                # "results": filtered_results,
            },
            status=status.HTTP_202_ACCEPTED,
        )


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
