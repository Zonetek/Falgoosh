import uuid
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import (
    AbstractBaseUser,
    Permission,
    PermissionsMixin,
    Group,
)


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username must be set")
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not password:
            raise ValueError("Superusers must have a password")

        return self.create_user(username, email, password, **extra_fields)

    def get_by_natural_key(self, username):
        return self.get(username=username)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=16, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name="user permissions",
        blank=True,
        related_name="user_permissions_set",
        help_text="Specific permissions for this user.",
        related_query_name="user_permissions",
    )

    groups = models.ManyToManyField(
        Group,
        verbose_name="groups",
        blank=True,
        related_name="groups_permissions",
        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
        related_query_name="groups_permissions",
    )

    # Explicitly set the objects manager at the class level
    objects = CustomUserManager()

    # Ensure these fields are defined for the manager to work
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name_plural = "Users"

    def __str__(self):
        if self.username is not None:
            return self.username
        else:
            return ""


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="profile"
    )

    # Lifetime counters (never reset) — useful for analytics
    total_scans = models.PositiveBigIntegerField(default=0)
    total_api_calls = models.PositiveBigIntegerField(default=0)

    # Security & account metadata
    is_verified = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    last_password_change = models.DateTimeField(null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)

    # last login/device info
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_country = models.CharField(max_length=2, null=True, blank=True)
    last_device = models.CharField(max_length=150, null=True, blank=True)

    # flexible user prefs
    preferences = models.JSONField(default=dict, blank=True)

    # soft-delete / anonymization hooks
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    anonymized = models.BooleanField(default=False)
    anonymized_at = models.DateTimeField(null=True, blank=True)

    # session id for single-session or device tracking
    session_id = models.UUIDField(default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return f"{self.user.username} Profile"

    def get_username(self):
        return self.user.username

    def get_email(self):
        return self.user.email

    @property
    def subscription(self):
        """Return the user's subscription instance if it exists (or None)."""
        return getattr(self.user, "subscription", None)

    def has_active_subscription(self) -> bool:
        sub = self.subscription
        return bool(sub and sub.is_active())

    def remaining_scans(self) -> int:
        """Delegate to subscription.remaining_scans() when available, otherwise 0."""
        sub = self.subscription
        if not sub:
            return 0
        return sub.remaining_scans()

    def remaining_api_calls(self) -> int:
        sub = self.subscription
        if not sub:
            return 0
        return sub.remaining_queries()

    def consume_scan(self, count: int = 1) -> bool:
        """Consume scan quota on the active subscription and update lifetime counters.

        Returns True when consumption succeeded, False otherwise.
        """
        sub = self.subscription
        if not sub or not sub.is_active():
            return False
        ok = sub.consume_scans(count=count)
        if ok:
            # update lifetime counter
            self.total_scans = models.F("total_scans") + count
            self.save(update_fields=["total_scans"])
            self.refresh_from_db(fields=["total_scans"])
        return ok

    def consume_api_calls(self, count: int = 1) -> bool:
        sub = self.subscription
        if not sub or not sub.is_active():
            return False
        ok = sub.consume_queries(count=count)
        if ok:
            self.total_api_calls = models.F("total_api_calls") + count
            self.save(update_fields=["total_api_calls"])
            self.refresh_from_db(fields=["total_api_calls"])
        return ok

    def reset_profile_usage(self):
        """Reset lifetime counters and subscription usage (for admin/maintenance).

        Use with care — keeping lifetime counters is recommended for analytics.
        """
        self.total_scans = 0
        self.total_api_calls = 0
        self.save(update_fields=["total_scans", "total_api_calls"])
        sub = self.subscription
        if sub:
            sub.reset_usage()

    def mark_deleted(self, anonymize: bool = True):
        """Soft-delete the profile; optionally anonymize PII.

        This keeps invoices and purchase history for compliance while removing
        identifying information from the user-facing profile.
        """

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

        if anonymize:
            # remove PII from profile only — do not delete invoices/purchase history
            self.anonymized = True
            self.anonymized_at = timezone.now()
            self.preferences = {}
            self.last_login_ip = None
            self.last_login_country = None
            self.last_device = None
            self.save(
                update_fields=[
                    "anonymized",
                    "anonymized_at",
                    "preferences",
                    "last_login_ip",
                    "last_login_country",
                    "last_device",
                ]
            )

            # Optionally anonymize the User record (email/username) — administratively controlled
            try:
                user = self.user
                if hasattr(user, "email"):
                    user.email = f"deleted+{user.id}@example.invalid"
                if hasattr(user, "username"):
                    user.username = f"deleted_{user.id}"
                user.is_active = False
                user.save(update_fields=["email", "username", "is_active"])
            except Exception:
                # swallow errors — keep records stable
                pass

    def restore_from_deletion(self):
        self.is_deleted = False
        self.anonymized = False
        self.deleted_at = None
        self.anonymized_at = None
        self.save(
            update_fields=["is_deleted", "anonymized", "deleted_at", "anonymized_at"]
        )
