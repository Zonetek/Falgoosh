from django.contrib import admin
from api_applications.shared_models.models import CustomUser, UserProfile
from api_applications.shared_models.models import Scan

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email')

@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'target_ip', 'status', 'created_at')
    search_fields = ('target_ip', 'user__username')
    list_filter = ('status', 'country', 'organization')
