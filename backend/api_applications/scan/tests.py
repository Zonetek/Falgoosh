from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.test import TestCase
from api_applications.shared_models.models.scan import Scan, ScanHistory
from api_applications.shared_models.models import CustomUser
from api_applications.scan.serializers import ScanSerializer, ScanHistorySerializer , ScanSearchSerializer

User = get_user_model()

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

class SearchIPTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", password="pass", email="test@example.com"
        )
        self.client = APIClient()
        self.url = reverse("search_ip")

    def test_missing_ip(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing", resp.data["error"])

    def test_invalid_ip(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url, {"ip": "not_an_ip"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["error"], "Invalid IP address format")

    def test_anonymous_no_record(self):
        resp = self.client.get(self.url, {"ip": "203.0.113.5"})
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))
        self.assertEqual(Scan.objects.count(), 0)
        self.assertEqual(ScanHistory.objects.count(), 0)

    def test_authenticated_creates_scan_and_history(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url, {"ip": "203.0.113.5"})
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))
        scan = Scan.objects.get(user=self.user, target_ip="203.0.113.5")
        histories = ScanHistory.objects.filter(scan=scan)
        self.assertTrue(histories.exists())

class UserScansAndHistoryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="pass1234",
            email="test@example.com"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.scan = Scan.objects.create(
            user=self.user,
            target_ip="8.8.8.8",
            target_ports="80,443",
            status="completed"
        )

        ScanHistory.objects.create(
            user=self.user,
            scan=self.scan,
            action="completed",
            details={"note": "Test scan completed"}
        )

        self.url_scans = reverse("user_scans")  
        self.url_history = reverse("user_scan_history", args=[self.scan.id])  

    def test_list_user_scans(self):
        resp = self.client.get(self.url_scans)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["target_ip"], "8.8.8.8")

    def test_list_user_scan_history(self):
        resp = self.client.get(self.url_history)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["action"], "completed")

    def test_history_not_found_for_invalid_scan(self):
        invalid_url = reverse("user_scan_history", args=[999])
        resp = self.client.get(invalid_url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", resp.data)