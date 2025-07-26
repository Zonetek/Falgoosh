import ipaddress
import logging

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api_applications.shared_libs.mongo_fetch_result import fetch_by_ip

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

        if ip_data:
            return Response(ip_data)
        else:
            return Response(
                {"message": f"No data found for IP: {ip}"},
                status=status.HTTP_404_NOT_FOUND,
            )
