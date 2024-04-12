from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages
from django.db.models import Count
from django.shortcuts import redirect

from common.model_admin import ModelAdmin, TaskAdmin
from common.permissions import has_model_permission
from events.models import (
    Event,
    LoadEventsFromKronosTask,
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
    ordering = ("-created_on",)

    def has_add_permission(self, request):
        return False


@admin.register(RegistrationStatus)
class RegistrationStatusAdmin(ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    list_display_links = ("name",)


@admin.register(RegistrationRole)
class RegistrationRoleAdmin(ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    list_display_links = ("name",)


@admin.register(RegistrationTag)
class RegistrationTagAdmin(ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    list_display_links = ("name",)


@admin.register(Registration)
class RegistrationAdmin(ModelAdmin):
    search_fields = [
        "event__title",
        "contact__first_name",
        "contact__last_name",
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


@admin.register(Event)
class EventAdmin(ModelAdmin):
    search_fields = (
        "code",
        "title",
        "venue_city",
        "venue_country__code",
        "venue_country__name",
        "dates",
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
    )
    autocomplete_fields = (
        "venue_country",
        "group",
    )
    list_filter = (
        AutocompleteFilterFactory("venue country", "venue_country"),
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
    actions = ["load_contacts_from_kronos"]

    @admin.display(description="Registrations", ordering="registration_count")
    def registrations_count(self, obj):
        return self.get_related_link(
            obj, "registrations", "event", obj.registration_count
        )

    def has_load_contacts_from_kronos_permission(self, request):
        return self.has_add_permission(request) and has_model_permission(
            request, LoadParticipantsFromKronosTask, "add"
        )

    @admin.action(
        description="Load participants from Kronos for selected events",
        permissions=["load_contacts_from_kronos"],
    )
    def load_contacts_from_kronos(self, request, queryset):
        tasks = []
        for event in queryset:
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