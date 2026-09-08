"""Admin de usuarios y perfiles."""

from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Administración de perfiles de usuario (roles y tenants)."""

    list_display = ("user", "role", "tenant")
    list_filter = ("role",)
    search_fields = ("user__email", "user__username")
