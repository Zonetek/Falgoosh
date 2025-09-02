from django.contrib import admin
from api_applications.shared_models.models.user import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "is_verified",
        "last_login_ip",
        "session_id",
        "created_at",
        "updated_at",
    )
