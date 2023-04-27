from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django_otp import devices_for_user
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice

from .forms import UserCreationForm, UserChangeForm
from .models import User


admin.site.unregister(StaticDevice)
admin.site.unregister(TOTPDevice)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    add_form = UserCreationForm
    form = UserChangeForm
    search_fields = ("email",)
    ordering = ("email",)
    list_display = (
        "email",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "email",
        "is_staff",
        "is_active",
    )
    readonly_fields = ("last_login",)
    actions = ("reset_2fa",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "last_login",
                )
            },
        ),
        (
            "Django Admin Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                )
            },
        ),
        (
            "Site permissions",
            {
                "fields": (
                    "can_view",
                    "can_edit",
                    "can_import",
                    "can_send_mail",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                    "can_view",
                    "can_edit",
                    "can_import",
                    "can_send_mail",
                    "groups",
                ),
            },
        ),
    )

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
