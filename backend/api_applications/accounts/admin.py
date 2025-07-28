from django.contrib import admin
from api_applications.shared_models.models import CustomUser, UserProfile

admin.site.register(CustomUser)
admin.site.register(UserProfile)
