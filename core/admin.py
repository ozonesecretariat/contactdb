from django.contrib import admin
from django_task.admin import TaskAdmin

from core.models import (
    SendMailTask,
    Organization,
    RegistrationStatus,
    Record,
    Group,
    Emails,
    LoadKronosEventsTask,
    KronosEvent,
    LoadKronosParticipantsTask,
    ResolveAllConflictsTask,
    EmailTag,
    EmailTemplate,
    EmailFile,
)


@admin.register(SendMailTask)
class SendMailTaskAdmin(TaskAdmin):
    search_fields = [
        "email",
    ]
    list_display = [
        "__str__",
        "email",
    ]
    ordering = ("-created_on",)


@admin.register(LoadKronosEventsTask)
class LoadKronosEventsTaskAdmin(TaskAdmin):
    list_display = [
        "__str__",
        "created_on",
        "duration_display",
        "status_display",
    ]
    ordering = ("-created_on",)

    def get_list_display(self, request):
        fields = super().get_list_display(request)
        fields.remove("log_link_display")
        return fields


@admin.register(LoadKronosParticipantsTask)
class LoadKronosParticipantsTaskAdmin(TaskAdmin):
    list_display = [
        "__str__",
        "created_on",
        "duration_display",
        "status_display",
    ]
    ordering = ("-created_on",)

    def get_list_display(self, request):
        fields = super().get_list_display(request)
        fields.remove("log_link_display")
        return fields


@admin.register(ResolveAllConflictsTask)
class ResolveAllConflictsTaskAdmin(TaskAdmin):
    list_display = [
        "__str__",
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
    search_fields = [
        "event__event_id",
        "status",
        "contact__first_name",
        "contact__last_name",
    ]
    list_display = ("contact", "event")
    list_filter = ["is_funded", "status", "role", "event"]


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


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(EmailFile)
class EmailFileAdmin(admin.ModelAdmin):
    list_display = ["name", "email"]
    search_fields = ["name"]


@admin.register(Emails)
class EmailsAdmin(admin.ModelAdmin):
    list_display = ["subject", "created_at"]
    ordering = ["-created_at"]
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "recipients",
                    "cc",
                    "groups",
                    "subject",
                    "content",
                    "send_personalised_emails",
                    "created_at",
                )
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("recipients", "cc", "groups", "subject")
        return self.readonly_fields


@admin.register(KronosEvent)
class KronosEventAdmin(admin.ModelAdmin):
    search_fields = ["event_id", "title"]
    list_display = [
        "event_id",
        "title",
        "code",
        "start_date",
        "end_date",
        "venue_country",
        "venue_city",
        "dates",
    ]
    list_filter = ["venue_country", "start_date", "end_date"]


@admin.register(EmailTag)
class EmailTagAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "field_name",
    ]
