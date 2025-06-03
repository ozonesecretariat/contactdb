from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages
from django.db.models import Count
from django.shortcuts import redirect
from django.utils.html import format_html
from import_export.admin import ExportMixin

from common.model_admin import ModelAdmin, TaskAdmin
from common.permissions import has_model_permission
from common.urls import reverse
from events.models import (
    Event,
    EventGroup,
    EventInvitation,
    LoadEventsFromKronosTask,
    LoadOrganizationsFromKronosTask,
    LoadParticipantsFromKronosTask,
    Registration,
    RegistrationRole,
    RegistrationStatus,
    RegistrationTag,
)


@admin.register(LoadEventsFromKronosTask)
class LoadEventsFromKronosTaskAdmin(TaskAdmin):
    """Task that imports all available events from Kronos.
    Events that are already present will have their attributes updated.
    """

    list_display = [
        "__str__",
        "created_on",
        "duration_display",
        "status_display",
    ]
    list_filter = (
        "created_on",
        "status",
    )
    ordering = ("-created_on",)


@admin.register(LoadParticipantsFromKronosTask)
class LoadParticipantsFromKronosTaskAdmin(TaskAdmin):
    """Import contacts and registrations from Kronos.
    Contacts that have conflict data will be added as temporary contacts in
    "Resolve Conflicts"
    """

    search_fields = ("event__title__unaccent",)
    list_display = [
        "event",
        "created_on",
        "duration_display",
        "status_display",
        "contacts_nr",
        "registrations_nr",
        "conflicts_nr",
        "skipped_nr",
    ]
    list_filter = (
        AutocompleteFilterFactory("event", "event"),
        "created_on",
        "status",
    )
    autocomplete_fields = ("event",)
    prefetch_related = ("event",)
    ordering = ("-created_on",)

    def has_add_permission(self, request):
        return False


@admin.register(LoadOrganizationsFromKronosTask)
class LoadOrganizationsFromKronosTaskAdmin(TaskAdmin):
    """Import organizations from Kronos that were not imported together
    with events.
    """

    list_display = [
        "created_on",
        "duration_display",
        "status_display",
        "organizations_nr",
        "contacts_nr",
        "skipped_contacts_nr",
    ]
    list_filter = (
        "created_on",
        "status",
    )
    ordering = ("-created_on",)

    def has_add_permission(self, request):
        return False


@admin.register(RegistrationStatus)
class RegistrationStatusAdmin(ExportMixin, ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    list_display_links = ("name",)


@admin.register(RegistrationRole)
class RegistrationRoleAdmin(ExportMixin, ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    list_display_links = ("name",)


@admin.register(RegistrationTag)
class RegistrationTagAdmin(ExportMixin, ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    list_display_links = ("name",)


@admin.register(Registration)
class RegistrationAdmin(ModelAdmin):
    ordering = ("contact__first_name", "contact__last_name", "event__title")
    search_fields = [
        "event__title",
        "contact__first_name",
        "contact__last_name",
        "contact__emails",
        "contact__email_ccs",
        "status__name",
        "role__name",
    ]
    list_display_links = ("contact", "event")
    list_display = (
        "contact",
        "event",
        "status",
        "role",
        "is_funded",
        "tags_display",
    )
    list_filter = [
        AutocompleteFilterFactory("event", "event"),
        AutocompleteFilterFactory("contact", "contact"),
        AutocompleteFilterFactory("status", "status"),
        AutocompleteFilterFactory("role", "role"),
        AutocompleteFilterFactory("tags", "tags"),
        "is_funded",
    ]
    autocomplete_fields = ("contact", "event", "role", "status", "tags")
    prefetch_related = (
        "contact",
        "contact__organization",
        "role",
        "status",
        "tags",
    )

    @admin.display(description="Tags")
    def tags_display(self, obj: Registration):
        return ", ".join(map(str, obj.tags.all()))


@admin.register(EventGroup)
class EventGroupAdmin(ExportMixin, ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "description")
    list_display_links = ("name",)
    ordering = ("name",)
    prefetch_related = ("events",)


@admin.register(Event)
class EventAdmin(ExportMixin, ModelAdmin):
    search_fields = (
        "code",
        "title__unaccent",
        "venue_city",
        "venue_country__code",
        "venue_country__name__unaccent",
        "dates",
        "groups__name",
    )
    list_display_links = ("code", "title")
    list_display = (
        "code",
        "title",
        "venue_country",
        "venue_city",
        "start_date",
        "end_date",
        "dates",
        "registrations_count",
        "groups_display",
    )
    autocomplete_fields = ("venue_country", "groups")
    list_filter = (
        AutocompleteFilterFactory("venue country", "venue_country"),
        AutocompleteFilterFactory("groups", "groups"),
        "start_date",
        "end_date",
    )
    readonly_fields = ("event_id",)
    ordering = (
        "-start_date",
        "-end_date",
    )
    prefetch_related = (
        "venue_country",
        "registrations",
    )
    annotate_query = {
        "registration_count": Count("registrations"),
    }
    actions = ["load_contacts_from_kronos", "send_email"]

    @admin.display(description="Registrations", ordering="registration_count")
    def registrations_count(self, obj):
        return self.get_related_link(
            obj,
            "registrations",
            "event",
            f"{obj.registration_count} participants",
        )

    @admin.display(description="Event Groups")
    def groups_display(self, obj):
        return ", ".join(map(str, obj.groups.all()))

    def has_load_contacts_from_kronos_permission(self, request):
        return self.has_add_permission(request) and has_model_permission(
            request, LoadParticipantsFromKronosTask, "add"
        )

    @admin.action(
        description="Load participants from Kronos for selected events",
        permissions=["load_contacts_from_kronos"],
    )
    def load_contacts_from_kronos(self, request, queryset):
        if invalid_events := queryset.filter(event_id__isnull=True).count():
            self.message_user(
                request,
                f"{invalid_events} events not in Kronos where skipped",
                level=messages.WARNING,
            )

        if not (valid_events := list(queryset.filter(event_id__isnull=False))):
            return None

        tasks = []
        for event in valid_events:
            task = LoadParticipantsFromKronosTask.objects.create(
                event=event,
                created_by=request.user,
            )
            task.run(is_async=True)
            tasks.append(tasks)

        self.message_user(
            request,
            f"{len(tasks)} tasks scheduled",
            level=messages.SUCCESS,
        )
        return redirect(self.get_admin_list_link(LoadParticipantsFromKronosTask))

    @admin.action(
        description="Send email to participants of selected events",
        permissions=["view"],
    )
    def send_email(self, request, queryset):
        ids = ",".join(map(str, queryset.values_list("id", flat=True)))
        return redirect(reverse("admin:emails_email_add") + "?events=" + ids)


@admin.register(EventInvitation)
class EventInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "organization",
        "event_or_group",
        "country",
        "invitation_link",
        "link_accessed",
        "email_tasks_display",
        "created_at",
    )
    list_display_links = ("__str__",)

    list_filter = (
        AutocompleteFilterFactory("event", "event"),
        AutocompleteFilterFactory("event_group", "event_group"),
        AutocompleteFilterFactory("organization", "organization"),
        AutocompleteFilterFactory("country", "country"),
        "link_accessed",
    )

    readonly_fields = ("token", "link_accessed", "created_at", "invitation_link")

    search_fields = (
        "organization__name",
        "event__title",
        "event_group__name",
        "country__name",
    )

    autocomplete_fields = ("event", "event_group", "organization", "country")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("event_group", "event"),
                    ("organization", "country"),
                )
            },
        ),
        (
            "Invitation Details",
            {
                "fields": (
                    "token",
                    "invitation_link",
                    "link_accessed",
                    "created_at",
                )
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("email_tasks")

    @admin.display(description="Target")
    def event_or_group(self, obj):
        return obj.event_group or obj.event

    @admin.display(description="Invitation Link")
    def invitation_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.invitation_link,
            "View Invitation Link",
        )

    @admin.display(description="Email Tasks")
    def email_tasks_display(self, obj):
        tasks = obj.email_tasks.all()
        if not tasks:
            return "-"
        return format_html(
            '<a href="{}?invitation__id__exact={}">{} tasks</a>',
            reverse("admin:emails_sendemailtask_changelist"),
            obj.id,
            tasks.count(),
        )

    def save_model(self, request, obj, form, change):
        # Reset link_accessed when creating new invitation
        if not change:
            obj.link_accessed = False
        super().save_model(request, obj, form, change)
