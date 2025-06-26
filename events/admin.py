import django_rq
from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.html import format_html
from import_export.admin import ExportMixin

from common.model_admin import ModelAdmin, TaskAdmin
from common.permissions import has_model_permission
from common.urls import reverse
from emails.admin import CKEditorTemplatesBase
from events.jobs import resend_confirmation_email
from events.models import (
    Event,
    EventGroup,
    EventInvitation,
    LoadEventsFromKronosTask,
    LoadOrganizationsFromKronosTask,
    LoadParticipantsFromKronosTask,
    Registration,
    RegistrationRole,
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
        "status",
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
        AutocompleteFilterFactory("organization", "contact__organization"),
        AutocompleteFilterFactory("government", "contact__organization__government"),
        AutocompleteFilterFactory("contact", "contact"),
        "status",
        AutocompleteFilterFactory("role", "role"),
        AutocompleteFilterFactory("tags", "tags"),
        "is_funded",
    ]
    autocomplete_fields = ("contact", "event", "role", "tags")
    prefetch_related = (
        "contact",
        "contact__organization",
        "role",
        "tags",
    )
    actions = ["resend_confirmation_emails"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("contact", "role"),
                    ("event", "status", "tags"),
                    "date",
                    ("priority_pass_code", "is_funded"),
                )
            },
        ),
        (
            "Registrant's Organization Info (at the time of registration)",
            {
                "fields": (
                    "organization",
                    ("designation", "department"),
                )
            },
        ),
    )

    @admin.display(description="Tags")
    def tags_display(self, obj: Registration):
        return ", ".join(map(str, obj.tags.all()))

    @admin.action(
        description="Resend confirmation email for selected registrations",
        permissions=["change"],
    )
    def resend_confirmation_emails(self, request, queryset):
        count = 0
        for registration in queryset:
            # Queue instead of doing it instantly or in bulk as it will require
            # generating the qr or badge.
            django_rq.enqueue(resend_confirmation_email, registration.id)
            count += 1
        self.message_user(
            request, f"{count} confirmation emails have been queued for sending"
        )


@admin.register(EventGroup)
class EventGroupAdmin(ExportMixin, ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "description")
    list_display_links = ("name",)
    ordering = ("name",)
    prefetch_related = ("events",)


@admin.register(Event)
class EventAdmin(ExportMixin, CKEditorTemplatesBase):
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
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "code",
                    "title",
                    "groups",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "venue_country",
                    "venue_city",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "dates",
                )
            },
        ),
        (
            "Confirmation email",
            {
                "fields": (
                    "confirmation_subject",
                    "confirmation_content",
                )
            },
        ),
        (
            "Refuse email",
            {
                "fields": (
                    "refuse_subject",
                    "refuse_content",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("event_id",),
            },
        ),
    )

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

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(
            request, queryset, search_term
        )

        referrer = request.META.get("HTTP_REFERER", "")

        # Filter queryset for EmailAdmin model to include only events
        # that have at least one registration
        if "/admin/emails/email/" in referrer:
            queryset = queryset.filter(~Q(registrations=None))

        return queryset, may_have_duplicates


class FutureEventFilter(admin.SimpleListFilter):
    title = "Event Time"
    parameter_name = "event_time"

    def lookups(self, request, model_admin):
        return (
            ("future", "Future events"),
            ("past", "Past events"),
            ("all", "All events"),
        )

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup
                or (self.value() is None and lookup == "all"),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": title,
            }

    def queryset(self, request, queryset):
        today = timezone.now()

        if self.value() == "future":
            return queryset.filter(
                Q(event__start_date__gte=today)
                | Q(
                    event_group__isnull=False,
                    event_group__events__start_date__gte=today,
                )
            ).distinct()

        if self.value() == "past":
            future_ids = queryset.filter(
                Q(event__start_date__gte=today)
                | Q(
                    event_group__isnull=False,
                    event_group__events__start_date__gte=today,
                )
            ).values_list("id", flat=True)
            return queryset.exclude(id__in=future_ids)

        return queryset


class HasUnregisteredFilter(admin.SimpleListFilter):
    title = "Registration Status"
    parameter_name = "has_unregistered"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Has unregistered organizations"),
            ("no", "All organizations registered"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            # Get invitations where at least one organization did not register
            has_unregistered = []
            for invitation in queryset:
                if invitation.unregistered_organizations.exists():
                    has_unregistered.append(invitation.id)
            return queryset.filter(id__in=has_unregistered)

        if self.value() == "no":
            # Get invitations where all orgs have registered
            all_registered = []
            for invitation in queryset:
                if not invitation.unregistered_organizations.exists():
                    all_registered.append(invitation.id)
            return queryset.filter(id__in=all_registered)

        return queryset


@admin.register(EventInvitation)
class EventInvitationAdmin(ModelAdmin):
    list_display = (
        "__str__",
        "organization",
        "event_or_group",
        "country",
        "invitation_link",
        "is_for_future_event_display",
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
        FutureEventFilter,
        HasUnregisteredFilter,
        "link_accessed",
    )

    readonly_fields = (
        "token",
        "link_accessed",
        "created_at",
        "invitation_link",
        "unregistered_organizations_display",
    )

    search_fields = (
        "organization__name",
        "event__title",
        "event_group__name",
        "country__name",
        "token",
    )

    autocomplete_fields = ("event", "event_group", "organization", "country")

    @admin.display(description="Unregistered Organizations")
    def unregistered_organizations_display(self, obj):
        """Display organizations that haven't registered any contacts."""
        if not obj.pk:
            return "-"

        unregistered = obj.unregistered_organizations
        count = unregistered.count()

        if count == 0:
            return "All organizations have registered at least one contact."

        # Build HTML list of organizations with links to their admin pages
        org_list_html = ["<div>"]
        org_list_html.append(
            f"<strong>{count} organization(s) without registrations:</strong>"
        )
        org_list_html.append("<ul>")

        for org in unregistered:
            org_url = reverse("admin:core_organization_change", args=[org.pk])
            org_list_html.append(
                f'<li><a href="{org_url}" target="_blank">{org.name}</a></li>'
            )
        org_list_html.append("</ul>")
        org_list_html.append("</div>")
        return format_html("".join(org_list_html))

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
        (
            "Registration Status",
            {
                "classes": ("collapse",),
                "fields": ("unregistered_organizations_display",),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "event", "event_group", "organization", "country", "email_tasks"
            )
        )

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

    @admin.display(description="Future Event", boolean=True)
    def is_for_future_event_display(self, obj):
        """Display the future event property as an icon in the admin."""
        return obj.is_for_future_event

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
