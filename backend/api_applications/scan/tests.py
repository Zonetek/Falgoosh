from django.test import TestCase
from api_applications.shared_models.models.scan import Scan, CustomUser , ScanHistory
from api_applications.scan.serializers import ScanSerializer, ScanHistorySerializer , ScanSearchSerializer

class ScanSerializerTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="testuser", password="password123", email="test@gmail.com")
        self.scan = Scan.objects.create(
            user=self.user,
            target_ip="8.8.8.8",
            target_ports="22,80,443",
            scan_type="tcp_scan"
        )

    def test_scan_serializer_output(self):
        serializer = ScanSerializer(self.scan)
        data = serializer.data

        self.assertEqual(data["target_ip"], "8.8.8.8")
        self.assertEqual(data["user_username"], "testuser")
        self.assertIn("location_display", data)
        self.assertIn("has_geographic_data", data)

class ScanHistorySerializerTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="historyuser", password="123", email="test@gmail.com")
        self.scan = Scan.objects.create(
            user=self.user,
            target_ip="1.1.1.1",
            target_ports="80"
        )
        self.history = ScanHistory.objects.create(
            user=self.user,
            scan=self.scan,
            action="created",
            details={"note": "Test action"}
        )

    def test_scan_history_serializer_output(self):
        serializer = ScanHistorySerializer(self.history)
        data = serializer.data
        self.assertEqual(data["scan_target"], "1.1.1.1")
        self.assertEqual(data["action"], "created")
        self.assertIn("timestamp", data)

class ScanSearchSerializerTest(TestCase):
    def test_valid_search_data(self):
        data = {
            "ip": "1.1.1.1",
            "port": 80,
            "country": "US",
            "page": 2,
            "limit": 50
        }
        serializer = ScanSearchSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_port(self):
        data = {
            "ip": "1.1.1.1",
            "port": 70000  # Invalid port
        }
        serializer = ScanSearchSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("port", serializer.errors)