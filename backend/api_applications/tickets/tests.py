from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError
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
