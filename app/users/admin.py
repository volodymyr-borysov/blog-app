"""Admin configuration for the User model."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import PasswordResetToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for the custom User model.

    Extends Django's built-in UserAdmin with custom fields.
    """

    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("is_staff", "is_active", "date_joined")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "bio", "avatar_url")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2"),
            },
        ),
    )


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin interface for Password Reset Tokens."""

    list_display = (
        "user",
        "token_preview",
        "created_at",
        "expires_at",
        "is_active",
        "used_at",
    )
    list_filter = ("is_active", "created_at", "expires_at")
    search_fields = ("user__email", "user__username", "token")
    readonly_fields = ("token", "created_at", "expires_at", "used_at")
    ordering = ("-created_at",)

    def token_preview(self, obj):
        """Show first 10 characters of token."""
        return f"{obj.token[:10]}..." if obj.token else ""

    token_preview.short_description = "Token Preview"

    def has_add_permission(self, request):
        """Disable manual token creation through admin."""
        return False
