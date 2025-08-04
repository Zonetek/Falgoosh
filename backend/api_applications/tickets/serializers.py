from rest_framework import serializers
from django.conf import settings
from api_applications.shared_models.models import Ticket, TicketMessage


class TicketMessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = TicketMessage
        fields = [
            "id",
            "sender",
            "message",
            "attachment",
            "created_at"
        ]
        read_only_fields = ["id", "sender", "created_at"]

class TicketSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "user",
            "title",
            "description",
            "status",
            "created_at",
            "updated_at",
            "messages"
        ]
        read_only_fields = ["id", "user", "status", "created_at", "updated_at", "messages"]

class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "title",
            "description"
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        ticket = Ticket.objects.create(
            user=request.user,
            **validated_data
        )
        return ticket