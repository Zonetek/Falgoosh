from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import update_last_login
from config.settings.base import UPDATE_LAST_LOGIN
import uuid
from rest_framework import serializers
from api_applications.shared_models.models import UserProfile
from api_applications.billing.serializers import (
    PurchaseHistorySerializer,
    InvoiceSerializer,
)
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from .tasks import send_confirmation_email
from allauth.account.models import EmailAddress

User = get_user_model()


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


class CustomRegisterSerializer(RegisterSerializer):
    email = serializers.EmailField(required=True, allow_blank=False)

    def validate_email(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("Email is required.")
        if User.objects.filter(email__iexact=value.strip()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def save(self, request):
        user = super().save(request)
        
        # Make sure EmailAddress object is created and confirmed = False
        email_obj, created = EmailAddress.objects.get_or_create(
            user=user,
            email=user.email,
            defaults={"verified": False, "primary": True}
        )

        # Trigger async confirmation email
        send_confirmation_email.delay(email_obj.pk)

        return user

class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    purchases = PurchaseHistorySerializer(
        many=True, read_only=True, source="user.purchases"
    )
    invoices = InvoiceSerializer(many=True, read_only=True, source="user.invoices")

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "is_verified",
            "membership",
            "stripe_customer_id",
            "purchases",
            "invoices",
            "session_id",
            "scan_limit",
        ]
        read_only_fields = ["id", "user", "session_id"]
