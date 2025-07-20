from rest_framework import serializers
from django.contrib.auth.models import Group , Permission
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from django.db import transaction
from api_applications.shared_models.models import CustomUser, Scan


class AdminUserListSerializer(serializers.ModelSerializer):
    group_names = serializers.SerializerMethodField()
    scans_count = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'is_active', 
            'is_staff', 'is_superuser', 'date_joined', 
            'last_login', 'group_names', 'scans_count', 'role'
        ]

    def get_group_names(self, obj):
        return [group.name for group in obj.groups.all()]
        
    def get_scans_count(self,obj):
        return obj.scans.count()
        
    def get_role(self, obj):
        if obj.is_superuser:
            return 'Super Admin'
        elif obj.groups.filter(name = 'super_admin'):
            return 'Super Admin'
        elif obj.groups.filter(name = 'scan_admin'):
            return 'Scan Admin'
        elif obj.groups.filter(name = 'user_admin'):
            return 'User Admin'
        elif obj.is_staff:
            return 'Staff'
        else:
            return 'User'
            
class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    groups = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Group.objects.all(),
        required=False
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'is_active','groups',
        ]
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords must match.")
        return data
    
    def create(self, validated_data):
        groups_data = validated_data.pop('groups', [])
        validated_data.pop('password_confirm')
        validated_data['password'] = make_password(validated_data['password'])
        
        with transaction.atomic():
            user = CustomUser.objects.create(**validated_data)
            user.groups.set(groups_data)
        
        return user
    
class AdminUserDetailSerializer(serializers.ModelSerializer):
        password = serializers.CharField(write_only=True, required=False)
        recent_scans = serializers.SerializerMethodField()
        scan_stats = serializers.SerializerMethodField()
        groups = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Group.objects.all(),
        required=False
    )
        class Meta:
            model = CustomUser
            fields = [
            'id', 'username', 'email', 'is_active', 
            'is_staff', 'is_superuser', 'date_joined', 
            'last_login', 'groups', 'user_permissions', 
            'recent_scans','password' ,'scan_stats',
            ]
            extra_kwargs = {
                'password': {'write_only': True},
            }

        def get_recent_scans(self, obj):
            recent_scans = obj.scans.order_by('-created_at')[:5]
            return AdminScanListSerializer(recent_scans, many=True).data
        
        def get_scan_stats(self, obj):
            scans = obj.scans.all()
            return {
                'total': scans.count(),
                'completed': scans.filter(status='completed').count(),
                'running': scans.filter(status='running').count(),
                'failed': scans.filter(status='failed').count(),
                'pending': scans.filter(status='pending').count()
            }
        
        def update(self, instance, validated_data):
            groups_data = validated_data.pop('groups', None)
            password = validated_data.pop('password', None)
            
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            
            if password:
                instance.password = make_password(password)
            
            instance.save()
            
            if groups_data is not None:
                instance.groups.set(groups_data)
            
            return instance
        
class AdminScanListSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    port_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Scan
        fields = [
            'id', 'target_ip', 'target_ports', 'scan_type', 'status',
            'country', 'city', 'region', 'latitude', 'longitude',
            'domain', 'organization', 'isp', 'asn',
            'mongo_object_id', 'created_at', 'updated_at',
            'started_at', 'completed_at', 'notes',
            'user_username', 'user_email', 'location_display', 'has_geographic_data', 'port_count'
        ]

    def get_port_count(self, obj):
        return obj.get_port_count()
        
class AdminScanDetailSerializer(serializers.ModelSerializer):
    user = AdminUserListSerializer(read_only=True)
    
    class Meta:
        model = Scan
        fields = '__all__'

class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Permission.objects.all(),
        required=False
    )
    users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'users_count']
    
    def get_users_count(self, obj):
        return obj.user_set.count()

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']

class DashboardStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_scans = serializers.IntegerField()
    scans_today = serializers.IntegerField()
    running_scans = serializers.IntegerField()
    failed_scans = serializers.IntegerField()
    recent_users = AdminUserListSerializer(many=True)
    recent_scans = AdminScanListSerializer(many=True)
