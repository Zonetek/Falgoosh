import pytest
from django.contrib.auth.models import Group
from api_applications.shared_models.models import CustomUser
from api_applications.admin_tools.serializers import AdminUserListSerializer, AdminUserCreateSerializer

@pytest.mark.django_db
def test_admin_user_list_serializer_fields():
    user = CustomUser.objects.create_user(
        username='testuser',
        password='12345678',
        email='test@example.com'
    )
    group = Group.objects.create(name='scan_admin')
    user.groups.add(group)
    serializer = AdminUserListSerializer(user)
    data = serializer.data

    assert data['username'] == 'testuser'
    assert data['email'] == 'test@example.com'
    assert 'group_names' in data
    assert data['role'] == 'Scan Admin'

@pytest.mark.django_db
def test_admin_user_list_serializer_role_superuser():
    user = CustomUser.objects.create_user(
        username='superuser',
        password='12345678',
        email='super@example.com',
        is_superuser=True
    )
    serializer = AdminUserListSerializer(user)
    data = serializer.data
    assert data['role'] == 'Super Admin'

from api_applications.shared_models.models import Scan

@pytest.mark.django_db
def test_admin_user_list_serializer_scans_count():
    user = CustomUser.objects.create_user(
        username='testuser',
        password='12345678',
        email='test@example.com'
    )
    Scan.objects.create(user=user, target_ip="1.1.1.1", target_ports="22")
    Scan.objects.create(user=user, target_ip="2.2.2.2", target_ports="80")
    serializer = AdminUserListSerializer(user)
    data = serializer.data
    assert data['scans_count'] == 2

@pytest.mark.django_db
def test_admin_user_create_serializer_valid_data():
    group = Group.objects.create(name='user_admin')
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
        "is_active": True,
        "admin_role": "user_admin",
        "groups": [group.pk]
    }
    serializer = AdminUserCreateSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.groups.filter(name="user_admin").exists()

@pytest.mark.django_db
def test_admin_user_create_serializer_password_mismatch():
    data = {
        "username": "failuser",
        "email": "fail@example.com",
        "password": "abc123456",
        "password_confirm": "somethingelse",
        "is_active": True,
        "groups": []
    }
    serializer = AdminUserCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert "Passwords must match." in str(serializer.errors)