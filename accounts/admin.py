from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import Group
from django.db.models import Count
from django_otp import devices_for_user
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice
from common.model_admin import ModelAdmin

from .models import User

admin.site.unregister(StaticDevice)
admin.site.unregister(TOTPDevice)


@admin.register(User)
class UserAdmin(ModelAdmin):
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "user_groups",
        "permission_count",
        "is_superuser",
        "is_active",
        "last_login",
    )
    list_filter = (
        "groups",
        "is_active",
        "is_superuser",
    )
    autocomplete_fields = ("groups",)
    filter_horizontal = ("user_permissions",)
    exclude = ("password",)
    actions = ("reset_2fa",)

    prefetch_related = ("groups",)
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
                    "groups",
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

    @admin.display(description="User Groups")
    def user_groups(self, obj: User):
        return ",".join(map(str, obj.groups.all()))

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
