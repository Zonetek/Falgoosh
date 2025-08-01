from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from api_applications.shared_models.models.billing import SubscriptionPlan, Invoice
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()



def create_authenticated_user():
    user = User.objects.create_user(username="testuser", password="testpass")
    token = RefreshToken.for_user(user)
    return user, f"Bearer {str(token.access_token)}"


class BillingViewTests(APITestCase):

    def setUp(self):
        self.plan = SubscriptionPlan.objects.create(
            name="Basic", price=29.99, description="Basic plan"
        )
        self.user, self.auth_header = create_authenticated_user()
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=self.auth_header)

    def test_plan_list_view(self):
        response = self.client.get(reverse("plan-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), SubscriptionPlan.objects.count())
        self.assertEqual(response.data[0]["name"], self.plan.name)

    def test_create_checkout_view_success(self):
        response = self.client.post(reverse("checkout"), {"plan_id": self.plan.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("checkout_url", response.data)

    def test_create_checkout_view_invalid_plan(self):
        response = self.client.post(reverse("checkout"), {"plan_id": 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_checkout_view_no_auth(self):
        self.client.credentials()  # clear auth
        response = self.client.post(reverse("checkout"), {"plan_id": self.plan.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_list_view(self):
        Invoice.objects.create(user=self.user, invoice_number="INV-001", amount=29.99)
        response = self.client.get(reverse("invoice-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["invoice_number"], "INV-001")

    def test_invoice_detail_view(self):
        invoice = Invoice.objects.create(user=self.user, invoice_number="INV-002", amount=59.99)
        response = self.client.get(reverse("invoice-detail", args=[invoice.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["invoice_number"], "INV-002")

    def test_invoice_detail_view_unauthorized_access(self):
        other_user = User.objects.create_user(username="hacker", password="hackerpass")
        other_invoice = Invoice.objects.create(user=other_user, invoice_number="HACK-001", amount=100.00)

        response = self.client.get(reverse("invoice-detail", args=[other_invoice.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # should not leak
