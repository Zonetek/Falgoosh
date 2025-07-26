from rest_framework import serializers
from api_applications.shared_models.models.scan import Scan, ScanHistory


class ScanSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    location_display = serializers.ReadOnlyField()
    has_geographic_data = serializers.ReadOnlyField()
    port_count = serializers.SerializerMethodField()

    class Meta:
        model = Scan
        fields = [
            "id",
            "user",
            "user_username",
            "target_ip",
            "target_ports",
            "scan_type",
            "status",
            "mongo_object_id",
            "created_at",
            "updated_at",
            "started_at",
            "completed_at",
            "notes",
            "country",
            "city",
            "region",
            "latitude",
            "longitude",
            "domain",
            "organization",
            "isp",
            "asn",
            "location_display",
            "has_geographic_data",
            "port_count",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def get_port_count(self, obj):
        return obj.get_port_count()


class ScanHistorySerializer(serializers.ModelSerializer):
    scan_target = serializers.CharField(source="scan.target_ip", read_only=True)

    class Meta:
        model = ScanHistory
        fields = ["action", "timestamp", "details", "scan_target"]


class ScanSearchSerializer(serializers.Serializer):
    ip = serializers.IPAddressField(required=False)
    port = serializers.IntegerField(min_value=1, max_value=65535, required=False)
    service = serializers.CharField(max_length=100, required=False)
    country = serializers.CharField(max_length=50, required=False)
    city = serializers.CharField(max_length=100, required=False)
    organization = serializers.CharField(max_length=200, required=False)
    banner = serializers.CharField(max_length=500, required=False)
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    limit = serializers.IntegerField(
        min_value=1, max_value=100, required=False, default=20
    )
