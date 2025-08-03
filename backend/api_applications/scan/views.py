import ipaddress
import logging
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api_applications.shared_libs.mongo_fetch_result import fetch_by_ip
from api_applications.shared_models.models.scan import ScanHistory, Scan
from api_applications.scan.serializers import ScanSerializer, ScanHistorySerializer

logger = logging.getLogger(__name__)


class SearchIPView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ip = request.GET.get("ip")

        if not ip:
            return Response(
                {"error": "Missing required query parameter: 'ip'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            ipaddress.ip_address(ip) # check correct ip address format
        except ValueError:
            return Response(
                {"error": "Invalid IP address format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            ip_data = fetch_by_ip(ip) # fetch data by ip 
        except Exception as e:
            logger.error(f"[SearchIPView] Error during fetch: {e}")
            return Response(
                {"error": "Internal server error while processing request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        if request.user.is_authenticated:
            scan, created = Scan.objects.get_or_create(
                user = request.user,
                target_ip = ip,
                defaults={
                    "status" : "pending",
                }
            )
            if created:
                ScanHistory.objects.create(
                    user=request.user,
                    scan=scan,
                    action="created",
                    details={"note": "Scan record created"},
                )

            if ip_data:
                scan.status = "running"
                scan.started_at = timezone.now()
                scan.save(update_fields=["status", "started_at", "updated_at"])
                ScanHistory.objects.create(
                    user=request.user,
                    scan=scan,
                    action="running",
                    details={},
                )


                scan.status = "completed"
                scan.completed_at = timezone.now()
                scan.country = ip_data.get("country")
                scan.city = ip_data.get("city")
                scan.region = ip_data.get("region")
                scan.latitude = ip_data.get("latitude")
                scan.longitude = ip_data.get("longitude")
                scan.domain = ip_data.get("domain")
                scan.organization = ip_data.get("organization")
                scan.isp = ip_data.get("isp")
                scan.asn = ip_data.get("asn")
                scan.save()

                ScanHistory.objects.create(
                    user=request.user,
                    scan=scan,
                    action="completed",
                    details=ip_data,
                )

            else:
                scan.status = "failed"
                scan.save(update_fields=["status", "updated_at"])
                ScanHistory.objects.create(
                    user=request.user,
                    scan=scan,
                    action="no_data",
                    details={"ip": ip},
                )

        if ip_data:
            return Response(ip_data)
        else:
            return Response(
                {"message": f"No data found for IP: {ip}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        
class UserScansView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        scans = Scan.objects.filter(user=request.user).order_by('-created_at')
        serializer = ScanSerializer(scans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UserScanHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, scan_id):
        try:
            scan = Scan.objects.get(pk=scan_id, user=request.user)
        except Scan.DoesNotExist:
            return Response(
                {"error": "Scan not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        history_qs = ScanHistory.objects.filter(scan=scan).order_by('-timestamp')
        serializer = ScanHistorySerializer(history_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)