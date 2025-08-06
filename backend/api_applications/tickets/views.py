from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from api_applications.shared_models.models import Ticket, TicketMessage
from api_applications.tickets.serializers import TicketCreateSerializer, TicketSerializer, TicketMessageSerializer
from api_applications.admin_tools.permissions import HasGroup


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

class AdminTicketViewSet(viewsets.ModelViewSet):

    queryset = Ticket.objects.all().order_by("-created_at")
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated, HasGroup("super_admin")] 

    def get_queryset(self):
        queryset = self.queryset
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        ticket = self.get_object()

        serializer = TicketMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket, sender=request.user)

        if ticket.status in ["closed", "pending"]:
            ticket.status = "reviewing"
        elif ticket.status == "reviewing":
            ticket.status = "answered"

        ticket.save(update_fields=["status", "updated_at"])

        return Response({
            "message": "Reply added successfully",
            "ticket_status": ticket.status
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        ticket = self.get_object()
        new_status = request.data.get("status")

        if new_status not in dict(Ticket.STATUS_CHOICES).keys():
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        ticket.status = new_status
        ticket.save(update_fields=["status", "updated_at"])

        return Response({"message": f"Status changed to {new_status}"} ,status=status.HTTP_200_OK)
