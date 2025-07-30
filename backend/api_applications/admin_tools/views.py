from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from api_applications.admin_tools.permissions import HasGroup
from api_applications.admin_tools.serializers import *
from api_applications.scan.serializers import ScanHistorySerializer, ScanSerializer
from api_applications.shared_models.models.scan import Scan, ScanHistory
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.


class AdminUserViewSet(viewsets.ModelViewSet):
    permission_classes = [HasGroup('super_admin') | HasGroup('user_admin')]

    def get_queryset(self):
        return CustomUser.objects.select_related('userprofile').prefetch_related('groups', 'scans')

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminUserCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return AdminUserDetailSerializer
        return AdminUserListSerializer

    def list(self, request):
        queryset = self.get_queryset()

        search = request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) 
            )

        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        group = request.query_params.get('group')
        if group:
            queryset = queryset.filter(groups__name=group)

        ordering = request.query_params.get('ordering', '-date_joined')
        queryset = queryset.order_by(ordering)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()

        return Response({
            'message': f'User has been {"activated" if user.is_active else "deactivated"}',
            'is_active': user.is_active
        })

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get('new_password')

        if not new_password:
            return Response(
                {'error': 'New password is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password has been changed successfully.'})

    @action(detail=True, methods=['get'])
    def scan_history(self, request, pk=None):
        user = self.get_object()
        scans = user.scans.order_by('-created_at')

        status_filter = request.query_params.get('status')
        if status_filter:
            scans = scans.filter(status=status_filter)

        page = self.paginate_queryset(scans)
        if page is not None:
            serializer = AdminScanListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AdminScanListSerializer(scans, many=True)
        return Response(serializer.data)

class AdminScanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Scan.objects.select_related('user').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['target_ip', 'user__username', 'country', 'status']
    ordering_fields = ['created_at', 'status']
    permission_classes = [HasGroup('super_admin') | HasGroup('scan_admin')]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminScanDetailSerializer
        return AdminScanListSerializer

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        scan = self.get_object()
        history_qs = ScanHistory.objects.filter(scan=scan).select_related('user').order_by('-timestamp')
        page = self.paginate_queryset(history_qs)
        if page is not None:
            serializer = ScanHistorySerializer(page, many=True) 
            return self.get_paginated_response(serializer.data)
        serializer = ScanHistorySerializer(history_qs, many=True)
        return Response(serializer.data)