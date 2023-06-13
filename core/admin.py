from django.contrib import admin
from django_task.admin import TaskAdmin

from core.models import (
    SendMailTask,
    Organization,
    RegistrationStatus,
    Record,
    Group,
    Emails,
)


@admin.register(SendMailTask)
class SendMailTaskAdmin(TaskAdmin):
    search_fields = [
        "subject",
        "recipient",
    ]
    list_display = [
        "__str__",
        "recipient",
        "subject",
        "created_on",
        "duration_display",
        "status_display",
    ]
    ordering = ("-created_on",)

    def get_list_display(self, request):
        fields = super().get_list_display(request)
        fields.remove("log_link_display")
        return fields


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    search_fields = [
        "organization_id",
        "name",
        "acronym",
        "organization_type_id",
        "government",
        "government_name",
        "country",
        "country_name",
    ]
    list_filter = ["organization_type"]


@admin.register(RegistrationStatus)
class RegistrationStatusAdmin(admin.ModelAdmin):
    search_fields = ["event_id", "status", "contact__first_name", "contact__last_name"]
    list_display = ("contact", "event_id")
    list_filter = ["is_funded", "status", "role"]


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    search_fields = [
        "contact_id",
        "first_name",
        "last_name",
        "designation",
        "department",
        "organization__name",
    ]
    list_filter = ["is_in_mailing_list", "is_use_organization_address"]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Emails)
class EmailsAdmin(admin.ModelAdmin):
    list_display = ["title", "created_at"]
    ordering = ["-created_at"]
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "recipients",
                    "cc",
                    "title",
                    "content",
                    "created_at",
                )
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("recipients", "cc", "title")
        return self.readonly_fields
