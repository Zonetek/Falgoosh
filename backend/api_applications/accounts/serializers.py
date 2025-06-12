from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import update_last_login
from config.settings.base import UPDATE_LAST_LOGIN
import uuid
from rest_framework import serializers
from .models import CustomUser, UserProfile


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer to include additional user information."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        if not user.userprofile.session_id:
            user.userprofile.session_id = uuid.uuid4()
            user.userprofile.save()

        # Add custom claims
        token["username"] = user.username
        token["email"] = user.email
        token["jti"] = str(token["jti"])
        token["ip"] = user.userprofile.last_login_ip
        token["session_id"] = str(user.userprofile.session_id)
        token["role"] = "admin" if user.is_superuser else "user"
        token["is_verified"] = user.userprofile.is_verified
        token["scan_limit"] = getattr(user.userprofile, "scan_limit", 100)
        return token

    def validate(self, attrs):
        """Validate the incoming data."""
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.token)

        if UPDATE_LAST_LOGIN and self.user is not None:
            update_last_login(type(self.user), self.user)

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "is_verified",
            "session_id",
            "scan_limit",
        ]
        read_only_fields = ["id", "user", "session_id"]
