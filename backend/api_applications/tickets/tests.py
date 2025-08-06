from django.contrib.auth import get_user_model
from django.test import TestCase
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from api_applications.shared_models.models import Ticket, TicketMessage
from api_applications.tickets.serializers import (
    TicketSerializer,
    TicketCreateSerializer,
    TicketMessageSerializer
)

User = get_user_model()


class TicketSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="pass", email="test@example.com"
        )
        self.ticket = Ticket.objects.create(
            user=self.user,
            title="Test Ticket",
            description="Test description"
        )

    def test_ticket_serializer_read(self):
        serializer = TicketSerializer(instance=self.ticket)
        data = serializer.data
        self.assertEqual(data["user"], str(self.user))
        self.assertEqual(data["title"], "Test Ticket")
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["messages"], [])

    def test_ticket_with_messages(self):
        message = TicketMessage.objects.create(
            ticket=self.ticket,
            sender=self.user,
            message="Test message"
        )
        serializer = TicketSerializer(instance=self.ticket)
        self.assertEqual(len(serializer.data["messages"]), 1)
        self.assertEqual(serializer.data["messages"][0]["message"], "Test message")


class TicketCreateSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="creator", password="pass", email="creator@example.com"
        )

    def test_create_ticket_success(self):
        serializer = TicketCreateSerializer(
            data={"title": "New Ticket", "description": "New description"},
            context={"request": type("req", (), {"user": self.user})}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        ticket = serializer.save()
        self.assertEqual(ticket.user, self.user)
        self.assertEqual(ticket.title, "New Ticket")

    def test_create_ticket_missing_fields(self):
        serializer = TicketCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)
        self.assertIn("description", serializer.errors)


class TicketMessageSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="messenger", password="pass", email="msg@example.com"
        )
        self.ticket = Ticket.objects.create(
            user=self.user,
            title="Ticket with message",
            description="desc"
        )
        self.message = TicketMessage.objects.create(
            ticket=self.ticket,
            sender=self.user,
            message="Hello world"
        )

    def test_message_serializer_read(self):
        serializer = TicketMessageSerializer(instance=self.message)
        data = serializer.data
        self.assertEqual(data["sender"], str(self.user))
        self.assertEqual(data["message"], "Hello world")
        self.assertIn("created_at", data)

class UserTicketViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1", password="pass123", email="user1@example.com"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.ticket = Ticket.objects.create(
            user=self.user,
            title="Test Ticket",
            description="Some description"
        )

    def test_create_ticket(self):
        url = reverse("user-tickets-list")
        data = {"title": "New Ticket", "description": "Ticket description"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ticket.objects.count(), 2)

    def test_list_tickets_only_own(self):
        other_user = User.objects.create_user(
            username="user2", password="pass123", email="user2@example.com"
        )
        Ticket.objects.create(user=other_user, title="Other Ticket", description="...")

        url = reverse("user-tickets-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_ticket_detail(self):
        url = reverse("user-tickets-detail", args=[self.ticket.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test Ticket")


class AdminTicketViewTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin", password="pass123", email="admin@example.com"
        )

        ticket_admin_group, _ = Group.objects.get_or_create(name="ticket_admin")
        self.admin_user.groups.add(ticket_admin_group)

        self.client = APIClient()
        self.client.force_authenticate(self.admin_user)

        self.ticket = Ticket.objects.create(
            user=self.admin_user,
            title="Admin Test Ticket",
            description="Some admin ticket description"
        )

    def test_admin_list_all_tickets(self):
        url = reverse("admin-tickets-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_admin_change_status(self):
        url = reverse("admin-tickets-change-status", args=[self.ticket.id])
        data = {"status": "reviewing"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "reviewing")

    def test_admin_reply_ticket(self):
        url = reverse("admin-tickets-reply", args=[self.ticket.id])
        data = {"message": "This is an admin reply."}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)