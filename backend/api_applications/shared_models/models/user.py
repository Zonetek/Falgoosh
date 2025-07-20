import uuid
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
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
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name_plural = "Users"

    def __str__(self):
        if self.username is not None:
            return self.username
        else:
            return ""


class UserProfile(models.Model):
    """TODO
    add related subscription model
    """

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    scan_limit = models.IntegerField(default=0)
    api_calls_remaining = models.IntegerField(default=100)
    is_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    session_id = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"

    def get_username(self):
        return self.user.username

    def get_email(self):
        return self.user.email

    

