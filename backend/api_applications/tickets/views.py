from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from api_applications.shared_models.models import Ticket, TicketMessage
from api_applications.tickets.serializers import TicketCreateSerializer, TicketSerializer, TicketMessageSerializer

class TicketViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == "create":
            return TicketCreateSerializer
        return TicketSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_message(self, request, pk=None):
        ticket = self.get_object()

        if ticket.status == "closed":
            return Response(
                {"error": "Cannot add message to a closed ticket."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TicketMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket, sender=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)