from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django_otp import devices_for_user
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice
from common.model_admin import ModelAdmin

from .models import User, Role
from .tasks import reset_password

admin.site.unregister(Group)
admin.site.unregister(StaticDevice)
admin.site.unregister(TOTPDevice)


@admin.register(Role)
class RoleAdmin(GroupAdmin):
    pass


@admin.register(User)
class UserAdmin(ModelAdmin):
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "user_roles",
        "permission_count",
        "is_superuser",
        "is_active",
        "last_login",
    )
    list_filter = (
        AutocompleteFilterFactory("roles", "roles"),
        "is_active",
        "is_superuser",
    )
    autocomplete_fields = ("roles",)
    filter_horizontal = ("user_permissions",)
    exclude = ("password",)

    prefetch_related = ("roles",)
    annotate_query = {
        "permission_count": Count("user_permissions"),
    }
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "is_active",
                ),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_superuser",
                    "roles",
                    "user_permissions",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "last_login",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    readonly_fields = ("last_login", "created_at", "updated_at")
    actions = ("reset_2fa", "reset_password_bulk")

    @admin.display(description="User Roles")
    def user_roles(self, obj: User):
        return ",".join(map(str, obj.roles.all()))

    @admin.display(description="User permissions", ordering="permission_count")
    def permission_count(self, obj):
        return f"{obj.permission_count} permission(s)"

    @admin.action(description="Reset 2FA for selected users")
    def reset_2fa(self, request, queryset):
        for user in queryset:
            for device in devices_for_user(user):
                device.delete()
        self.message_user(
            request,
            "2FA has been disabled for selected users",
            level=messages.SUCCESS,
        )

    @admin.action(description="Reset password")
    def reset_password_bulk(self, request, queryset):
        for obj in queryset:
            reset_password.delay(obj.email)

        self.message_user(
            request,
            f"Email sent to {queryset.count()} accounts for password reset",
            level=messages.SUCCESS,
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not change:
            reset_password.delay(obj.email)
            self.message_user(
                request,
                f"Email sent to {obj} for password reset",
                level=messages.SUCCESS,
            )
