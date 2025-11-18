import base64

import django_rq
from admin_auto_filters.filters import AutocompleteFilterFactory
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Max, Min, Q
from django.forms.models import BaseInlineFormSet
from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from import_export.admin import ExportMixin

from common.model_admin import ModelAdmin, ModelResource, TaskAdmin
from common.pdf import print_pdf
from common.permissions import has_model_permission
from common.urls import reverse
from core.models import Contact, Organization
from emails.admin import CKEditorTemplatesBase
from emails.models import SendEmailTask
from events.exports.dsa import DSAFiles, DSAReport
from events.exports.list_of_participants import ListOfParticipants
from events.exports.statistics import PostMeetingStatistics, PreMeetingStatistics
from events.jobs import send_priority_pass_status_emails
from events.models import (
    DSA,
    Event,
    EventGroup,
    EventInvitation,
    LoadEventsFromKronosTask,
    LoadOrganizationsFromKronosTask,
    LoadParticipantsFromKronosTask,
    PriorityPass,
    Registration,
    RegistrationRole,
    RegistrationTag,
)


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
    list_display = ("name", "sort_order", "hide_for_nomination", "hide_in_lop")
    list_display_links = ("name",)


@admin.register(RegistrationTag)
class RegistrationTagAdmin(ExportMixin, ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "protected")
    list_display_links = ("name",)
    readonly_fields = ("protected",)

    def has_change_permission(self, request, obj=None):
        if obj and obj.protected:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.protected:
            return False
        return super().has_delete_permission(request, obj)


class RegistrationResource(ModelResource):
    prefetch_related = (
        "dsa",
        "tags",
        "role",
        "priority_pass",
        "contact",
        "contact__groups",
        "event",
        "organization",
        "organization__country",
        "organization__country__region",
        "organization__country__subregion",
        "organization__government",
        "organization__government__region",
        "organization__government__subregion",
        "organization__organization_type",
        "organization__primary_contacts",
        "organization__secondary_contacts",
    )

    class Meta:
        model = Registration
        fields = [
            *ModelResource.expand_all_fields(Registration),
            *ModelResource.expand_all_fields(DSA, prefix="dsa__"),
            "tags",
            *ModelResource.expand_all_fields(RegistrationRole, prefix="role__"),
            *ModelResource.expand_all_fields(PriorityPass, prefix="priority_pass__"),
            *ModelResource.expand_all_fields(Contact, prefix="contact__"),
            "contact__groups",
            *ModelResource.expand_all_fields(
                Event,
                prefix="event__",
                exclude=[
                    "event__confirmation_subject",
                    "event__refusal_subject",
                ],
            ),
            *ModelResource.expand_all_fields(
                Organization, prefix="organization__", max_depth=2
            ),
            "organization__primary_contacts",
            "organization__secondary_contacts",
        ]

    def dehydrate_tags(self, obj):
        return ", ".join(t.name for t in obj.tags.all())

    def dehydrate_contact__groups(self, obj):
        return ", ".join(g.name for g in obj.contact.groups.all())

    def dehydrate_organization__primary_contacts(self, obj):
        if not obj.organization:
            return ""
        return ", ".join(c.full_name for c in obj.organization.primary_contacts.all())

    def dehydrate_organization__secondary_contacts(self, obj):
        if not obj.organization:
            return ""
        return ", ".join(c.full_name for c in obj.organization.secondary_contacts.all())


@admin.register(Registration)
class RegistrationAdmin(ExportMixin, ModelAdmin):
    resource_class = RegistrationResource
    ordering = (
        "event",
        "organization__government",
        "sort_order",
        "role__sort_order",
        "contact__last_name",
        "contact__first_name",
    )
    search_fields = [
        "event__title",
        "contact__first_name",
        "contact__last_name",
        "contact__emails",
        "contact__email_ccs",
        "status",
        "role__name",
        "priority_pass__code",
    ]
    list_display_links = ("contact__last_name", "contact__first_name", "event")
    list_display = (
        "contact__first_name",
        "contact__last_name",
        "event_code_link",
        "organization__government",
        "status",
        "role",
        "sort_order",
        "role__sort_order",
        "is_funded",
        "tags_display",
    )
    list_filter = [
        AutocompleteFilterFactory("event", "event"),
        AutocompleteFilterFactory("organization", "contact__organization"),
        AutocompleteFilterFactory("government", "contact__organization__government"),
        AutocompleteFilterFactory(
            "subregion", "contact__organization__country__subregion"
        ),
        AutocompleteFilterFactory(
            "organization type", "contact__organization__organization_type"
        ),
        AutocompleteFilterFactory("contact", "contact"),
        "status",
        AutocompleteFilterFactory("role", "role"),
        "has_credentials",
        "contact__needs_visa_letter",
        AutocompleteFilterFactory("tags", "tags"),
        "is_funded",
        AutocompleteFilterFactory("event group", "event__group"),
    ]
    autocomplete_fields = ("contact", "event", "role", "tags", "organization")
    prefetch_related = (
        "contact",
        "event",
        "contact__organization",
        "contact__organization__government",
        "contact__organization__country",
        "contact__organization__country__subregion",
        "contact__organization__organization_type",
        "role",
        "tags",
    )
    actions = ("send_email", "resend_confirmation_emails")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "contact",
                    "role",
                    "event",
                    "status",
                    "priority_pass",
                    "is_funded",
                    "date",
                )
            },
        ),
        (
            "Registrant's Organization Info (at the time of registration)",
            {
                "fields": (
                    "organization",
                    ("designation", "department"),
                    "has_credentials",
                    "credentials_display",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "sort_order",
                    "tags",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "priority_pass",
        "credentials_display",
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + (
                "contact",
                "event",
            )
        return self.readonly_fields

    @admin.display(description="Tags")
    def tags_display(self, obj: Registration):
        return ", ".join(map(str, obj.tags.all()))

    @admin.display(description="Event Code", ordering="event__code")
    def event_code_link(self, obj):
        if not obj.event:
            return "-"

        event_url = reverse("admin:events_event_change", args=[obj.event.pk])
        return format_html(
            '<a href="{}" target="_blank">{}</a>', event_url, obj.event.code
        )

    @admin.action(description="Send email to selected contacts", permissions=["view"])
    def send_email(self, request, queryset):
        ids = ",".join(
            map(
                str,
                queryset.values_list("contact__id", flat=True)
                .distinct("contact__id")
                .order_by("contact_id"),
            )
        )
        return redirect(reverse("admin:emails_email_add") + "?recipients=" + ids)

    @admin.display(description="Credentials")
    def credentials_display(self, obj):
        return self.get_encrypted_file_display(obj, "credentials")


class RegistrationInlineFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)

        # Disable showing add/edit/delete buttons for related "role"
        if "role" in form.fields:
            form.fields["role"].widget = forms.Select(
                choices=form.fields["role"].widget.choices
            )

        # Customize the DELETE field behavior for each form
        if (
            "DELETE" in form.fields
            and hasattr(form, "instance")
            and form.instance
            and form.instance.pk
        ):
            registration = form.instance

            # Only allow deletion for "placeholder" registrations
            can_delete = (
                registration.status == "" and registration.event.hide_for_nomination
            )
            if not can_delete:
                form.fields["DELETE"].disabled = True

    def clean(self):
        """
        Additional validation to prevent deletion of non-placeholder registrations.
        """
        super().clean()

        for form in self.forms:
            if (
                form.cleaned_data.get("DELETE")
                and hasattr(form, "instance")
                and form.instance
                and form.instance.pk
            ):
                registration = form.instance
                can_delete = (
                    registration.status == "" and registration.event.hide_for_nomination
                )

                if not can_delete:
                    if registration.status != "":
                        error_msg = f"Cannot delete registration with status '{registration.get_status_display()}'"
                    else:
                        error_msg = "Cannot delete registration for visible event"

                    form.add_error("DELETE", error_msg)


class RegistrationInline(admin.TabularInline):
    model = Registration
    formset = RegistrationInlineFormSet
    extra = 0
    max_num = 0
    fields = (
        "contact",
        "event",
        "role",
        "status",
    )
    readonly_fields = ("contact", "event")

    def save_model(self, request, obj, form, change):
        """
        Overridden to call full_clean before saving, which does not happen automatically
        for inlines.
        """
        try:
            obj.full_clean()
        except ValidationError as e:
            # If there are any validation errors, add them to the form
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            # And avoid calling super.save()
            if form.errors:
                return

        super().save_model(request, obj, form, change)


@admin.register(PriorityPass)
class PriorityPassAdmin(ModelAdmin):
    inlines = (RegistrationInline,)
    search_fields = (
        "code",
        "registrations__event__code",
        "registrations__event__title",
        "registrations__contact__first_name",
        "registrations__contact__last_name",
        "registrations__contact__emails",
        "registrations__contact__email_ccs",
        "registrations__contact__phones",
        "registrations__contact__organization__name",
        "registrations__organization__name",
    )
    list_display = (
        "code",
        "registrations_links",
        "pass_download_link",
        "badge_download_link",
        "created_at",
    )
    list_filter = (
        AutocompleteFilterFactory("event", "registrations__event"),
        AutocompleteFilterFactory("event group", "registrations__event__group"),
        "registrations__status",
        AutocompleteFilterFactory("contact", "registrations__contact"),
        AutocompleteFilterFactory(
            "organization", "registrations__contact__organization"
        ),
        AutocompleteFilterFactory(
            "organization type",
            "registrations__contact__organization__organization_type",
        ),
        AutocompleteFilterFactory(
            "government", "registrations__contact__organization__government"
        ),
    )
    fields = (
        "code",
        "pass_download_link",
        "badge_download_link",
        "created_at",
        "attach_priority_pass",
        "confirmation_email",
        "refused_email",
    )
    prefetch_related = (
        "registrations",
        "registrations__event",
        "registrations__contact",
        "registrations__contact__organization",
    )
    readonly_fields = (
        "code",
        "registrations_links",
        "pass_download_link",
        "badge_download_link",
        "created_at",
        "attach_priority_pass",
        "confirmation_email",
        "refused_email",
    )
    ordering = ("-created_at",)
    annotate_query = {
        "registration_count": Count("registrations"),
    }
    actions = ("send_confirmation_emails",)

    def has_delete_permission(self, request, obj=None):
        """Only allow deleting priority passes with no related registration"""
        if obj is None:
            return False
        return not obj.registrations.exists()

    def has_add_permission(self, request):
        return False

    @admin.display(description="Registrations", ordering="registration_count")
    def registrations_links(self, obj):
        return self.get_m2m_links(obj.registrations.all())

    @admin.display(description="Priority pass")
    def pass_download_link(self, obj):
        url = reverse("admin:priority_pass_view", args=[obj.id]) + "?pdf=true"
        url_download = url + "&download=true"
        return format_html(
            " | ".join(
                [
                    '<a href="{}" target="_blank">View</a>',
                    '<a href="{}" target="_blank">Download</a>',
                    '<a href="{}" target="_blank">Scan</a>',
                ]
            ),
            url,
            url_download,
            obj.qr_url,
        )

    @admin.display(description="Badge")
    def badge_download_link(self, obj):
        url = reverse("admin:badge_view", args=[obj.id]) + "?pdf=true"
        url_download = url + "&download=true"
        return format_html(
            " | ".join(
                [
                    '<a href="{}" target="_blank">View</a>',
                    '<a href="{}" target="_blank">Download</a>',
                    '<a href="{}" target="_blank">Scan</a>',
                ]
            ),
            url,
            url_download,
            obj.qr_url,
        )

    @admin.display(description="Attach priority pass", boolean=True)
    def attach_priority_pass(self, obj):
        return obj.main_event and obj.main_event.attach_priority_pass

    @admin.display(description="Confirmation email", boolean=True)
    def confirmation_email(self, obj):
        return obj.main_event and obj.main_event.has_confirmation_email

    @admin.display(description="Refused email", boolean=True)
    def refused_email(self, obj):
        return obj.main_event and obj.main_event.has_refused_email

    def get_urls(self):
        return [
            path(
                "<path:object_id>/pass/",
                self.admin_site.admin_view(self.pass_view),
                name="priority_pass_view",
            ),
            path(
                "<path:object_id>/badge/",
                self.admin_site.admin_view(self.badge_view),
                name="badge_view",
            ),
            *super().get_urls(),
        ]

    def pass_view(self, request, object_id):
        priority_pass = self.get_object(request, object_id)
        context = {
            **self.admin_site.each_context(request),
            **priority_pass.priority_pass_context,
        }
        if request.GET.get("pdf") == "true":
            return FileResponse(
                print_pdf(
                    priority_pass.priority_pass_template,
                    context=context,
                    request=request,
                ),
                content_type="application/pdf",
                filename=f"{priority_pass.code}.pdf",
                as_attachment=request.GET.get("download") == "true",
            )

        return TemplateResponse(request, priority_pass.priority_pass_template, context)

    def badge_view(self, request, object_id):
        priority_pass = self.get_object(request, object_id)
        context = {
            **self.admin_site.each_context(request),
            **priority_pass.priority_pass_context,
        }
        if request.GET.get("pdf") == "true":
            return FileResponse(
                print_pdf(
                    priority_pass.badge_template,
                    context=context,
                    request=request,
                ),
                content_type="application/pdf",
                filename=f"badge_{priority_pass.code}.pdf",
                as_attachment=request.GET.get("download") == "true",
            )

        return TemplateResponse(request, priority_pass.badge_template, context)

    def response_change(self, request, obj):
        resp = super().response_change(request, obj)
        if "_save_without_sending" not in request.POST:
            self.send_confirmation_emails(request, [obj])
        return resp

    @admin.action(
        description="Send confirmation email for selected priority passes",
        permissions=["change"],
    )
    def send_confirmation_emails(self, request, queryset):
        count = 0
        for priority_pass in queryset:
            # Queue instead of doing it instantly or in bulk as it will require
            # generating the qr or badge.
            django_rq.enqueue(send_priority_pass_status_emails, priority_pass.id)
            count += 1
        self.message_user(
            request, f"{count} confirmation emails have been queued for sending"
        )


class EventInline(admin.TabularInline):
    max_num = 0
    model = Event
    fields = readonly_fields = (
        "code",
        "event_link",
        "start_date",
        "end_date",
        "hide_for_nomination",
        "attach_priority_pass",
    )
    ordering = ("-start_date",)

    def has_delete_permission(self, request, obj=None):
        return False

    def event_link(self, obj):
        if not obj:
            return self.get_empty_value_display()

        url = reverse("admin:events_event_change", args=(obj.pk,))
        return format_html(
            '<a href="{url}">{link_text}</a>', url=url, link_text=obj.title or obj
        )

    event_link.short_description = "Event title"


@admin.register(EventGroup)
class EventGroupAdmin(ExportMixin, ModelAdmin):
    search_fields = ("name",)
    list_display = ("name", "description", "date_range")
    list_display_links = ("name",)
    ordering = ("-created_at",)
    prefetch_related = ("events",)
    inlines = [EventInline]

    def get_queryset(self, request):
        """Using event dates annotations for the list view"""
        return (
            super()
            .get_queryset(request)
            .annotate(
                start_date=Min("events__start_date"), end_date=Max("events__end_date")
            )
            .prefetch_related("events")
            .order_by("-start_date", "name")
        )

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(
            request, queryset, search_term
        )

        referrer = request.META.get("HTTP_REFERER", "")

        if "/admin/emails/invitationemail" in referrer:
            queryset = queryset.filter(
                events__isnull=False,
                events__end_date__gte=timezone.now(),
            ).distinct()

        return queryset, may_have_duplicates

    @admin.display(description="Dates", ordering="start_date")
    def date_range(self, obj):
        if hasattr(obj, "start_date") and obj.start_date:
            start_formatted = obj.start_date.strftime("%d %b %Y")
            if hasattr(obj, "end_date") and obj.end_date:
                end_formatted = obj.end_date.strftime("%d %b %Y")
                return f"{start_formatted} to {end_formatted}"
            return start_formatted
        return "-"


@admin.register(Event)
class EventAdmin(ExportMixin, CKEditorTemplatesBase):
    search_fields = (
        "code",
        "title__unaccent",
        "venue_city",
        "venue_country__code",
        "venue_country__name__unaccent",
        "dates",
        "group__name",
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
        "group",
        "documents",
    )
    autocomplete_fields = (
        "venue_country",
        "group",
    )
    list_filter = (
        AutocompleteFilterFactory("venue country", "venue_country"),
        AutocompleteFilterFactory("group", "group"),
        "start_date",
        "end_date",
    )
    readonly_fields = ("event_id", "documents")
    ordering = (
        "-start_date",
        "-end_date",
    )
    prefetch_related = (
        "venue_country",
        "registrations",
        "group",
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
                    "group",
                    "hide_for_nomination",
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
                    "timezone",
                    "start_date",
                    "end_date",
                    "dates",
                )
            },
        ),
        (
            "DSA",
            {
                "fields": (
                    "dsa",
                    "term_exp",
                )
            },
        ),
        (
            "Confirmation email",
            {
                "fields": (
                    "attach_priority_pass",
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
            "Badge information",
            {
                "fields": (
                    "event_logo",
                    "include_badge_back_side",
                    "wifi_name",
                    "wifi_password",
                    "app_store_url",
                    "play_store_url",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "event_id",
                    "documents",
                    "lop_doc_symbols",
                ),
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

    @admin.display(description="Documents")
    def documents(self, obj):
        return format_html(
            " | ".join(
                [
                    '<a href="{}" target="_blank">Pre Statistics</a>',
                    '<a href="{}" target="_blank">LoP</a>',
                    '<a href="{}" target="_blank">Post Statistics</a>',
                    '<a href="{}" target="_blank">DSA Report</a>',
                    '<a href="{}" target="_blank">DSA Files</a>',
                ]
            ),
            reverse("admin:pre_meeting_statistics", args=(obj.id,)),
            reverse("admin:lop", args=(obj.id,)),
            reverse("admin:post_meeting_statistics", args=(obj.id,)),
            reverse("admin:dsa", args=(obj.id,)),
            reverse("admin:dsa_files", args=(obj.id,)),
        )

    def get_urls(self):
        return [
            path(
                "<path:object_id>/pre-statistics/",
                self.admin_site.admin_view(self.get_pre_meeting_statistics),
                name="pre_meeting_statistics",
            ),
            path(
                "<path:object_id>/post-statistics/",
                self.admin_site.admin_view(self.get_post_meeting_statistics),
                name="post_meeting_statistics",
            ),
            path(
                "<path:object_id>/lop/",
                self.admin_site.admin_view(self.get_lop),
                name="lop",
            ),
            path(
                "<path:object_id>/dsa/",
                self.admin_site.admin_view(self.get_dsa),
                name="dsa",
            ),
            path(
                "<path:object_id>/dsa_files/",
                self.admin_site.admin_view(self.get_dsa_files),
                name="dsa_files",
            ),
            *super().get_urls(),
        ]

    def get_pre_meeting_statistics(self, request, object_id):
        event = self.get_object(request, object_id)
        return FileResponse(
            PreMeetingStatistics(event).export_docx(), as_attachment=True
        )

    def get_post_meeting_statistics(self, request, object_id):
        event = self.get_object(request, object_id)
        return FileResponse(
            PostMeetingStatistics(event).export_docx(), as_attachment=True
        )

    def get_lop(self, request, object_id):
        event = self.get_object(request, object_id)
        return FileResponse(ListOfParticipants(event).export_docx(), as_attachment=True)

    def get_dsa(self, request, object_id):
        event = self.get_object(request, object_id)
        return FileResponse(DSAReport(event).export_xlsx(), as_attachment=True)

    def get_dsa_files(self, request, object_id):
        event = self.get_object(request, object_id)
        return FileResponse(DSAFiles(event).export_zip(), as_attachment=True)

    def has_load_contacts_from_kronos_permission(self, request):
        return (
            settings.KRONOS_ENABLED
            and self.has_add_permission(request)
            and has_model_permission(request, LoadParticipantsFromKronosTask, "add")
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

        if "/admin/emails/invitationemail" in referrer:
            queryset = queryset.filter(end_date__gte=timezone.now())

        return queryset, may_have_duplicates

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "timezone":
            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            formfield.widget.attrs.update(
                {
                    "data-choice-select2": "true",
                }
            )
            return formfield
        return super().formfield_for_dbfield(db_field, request, **kwargs)


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
        "qr_code_display",
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
                    "qr_code_display",
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

    def get_deleted_objects(self, objs, request):
        """
        Overridden to allow deleting invitations.
        """
        # Get the standard deletion info for invitations
        (
            deleted_objects,
            model_count,
            perms_needed,
            protected,
        ) = super().get_deleted_objects(objs, request)

        permision_name = SendEmailTask._meta.verbose_name
        perms_needed.discard(permision_name)

        return deleted_objects, model_count, perms_needed, protected

    def delete_model(self, request, obj):
        """Overridden to show info on deleted related SendEmailTask objects."""
        deleted_task_count = obj.email_tasks.count()

        super().delete_model(request, obj)

        if deleted_task_count > 0:
            self.message_user(
                request,
                f"Deleted {deleted_task_count} related email task(s).",
                messages.SUCCESS,
            )

    def delete_queryset(self, request, queryset):
        """Overridden to show info on deleted related SendEmailTask objects."""
        deleted_task_count = SendEmailTask.objects.filter(
            invitation__in=queryset
        ).count()

        super().delete_queryset(request, queryset)

        if deleted_task_count > 0:
            self.message_user(
                request,
                f"Deleted {deleted_task_count} related send email task(s).",
                messages.SUCCESS,
            )

    @admin.display(description="Target")
    def event_or_group(self, obj):
        return obj.event_group or obj.event

    @admin.display(description="Invitation Link")
    def invitation_link(self, obj):
        qr_url = reverse("admin:events_eventinvitation_qr", args=[obj.pk])

        return format_html(
            '<a href="{}" target="_blank">View Invitation Link</a> | '
            '<a href="{}" target="_blank">QR Code</a>',
            obj.invitation_link,
            qr_url,
        )

    @admin.display(description="QR Code")
    def qr_code_display(self, obj):
        if not obj.pk:
            return "-"

        return format_html(
            '<div style="text-align: center;">'
            '<img src="{}" alt="QR Code" style="max-width: 200px; max-height: 200px;" />'
            "<br><small>Scan to access invitation</small>"
            "</div>",
            obj.invitation_link_qr_code,
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

    def get_urls(self):
        return [
            path(
                "<path:object_id>/qr/",
                self.admin_site.admin_view(self.qr_code_view),
                name="events_eventinvitation_qr",
            ),
            *super().get_urls(),
        ]

    def qr_code_view(self, request, object_id):
        invitation = self.get_object(request, object_id)

        data_url = invitation.invitation_link_qr_code
        # Removes the "data:image/png;base64," prefix
        img_data = data_url.split(",")[1]
        img_bytes = base64.b64decode(img_data)

        return HttpResponse(img_bytes, content_type="image/png")


@admin.register(DSA)
class DSAAdmin(ModelAdmin):
    list_display = (
        "registration",
        "umoja_travel",
        "bp",
        "arrival_date",
        "departure_date",
        "number_of_days",
        "cash_card",
        "paid_dsa",
    )
    list_filter = (
        AutocompleteFilterFactory("event", "registration__event"),
        "registration__status",
        "paid_dsa",
    )
    autocomplete_fields = ("registration",)
    prefetch_related = (
        "registration__contact",
        "registration__event",
        "registration__organization",
        "registration__organization__government",
        "registration__organization__country",
        "registration__organization__organization_type",
        "registration__contact__organization",
        "registration__contact__organization__government",
        "registration__contact__organization__country",
        "registration__contact__organization__organization_type",
    )
    search_fields = (
        "registration__contact__title",
        "registration__contact__first_name",
        "registration__contact__last_name",
        "registration__organization__name",
        "registration__event__title",
    )

    fields = (
        "registration",
        "umoja_travel",
        "bp",
        "arrival_date",
        "departure_date",
        "cash_card",
        "paid_dsa",
        "get_boarding_pass_display",
        "get_passport_display",
        "get_signature_display",
        "number_of_days",
        "dsa_on_arrival",
        "total_dsa",
    )

    readonly_fields = (
        "get_boarding_pass_display",
        "get_passport_display",
        "get_signature_display",
        "number_of_days",
        "dsa_on_arrival",
        "total_dsa",
    )

    @admin.display(description="Boarding pass")
    def get_boarding_pass_display(self, obj):
        return self.get_encrypted_file_display(obj, "boarding_pass")

    @admin.display(description="Passport")
    def get_passport_display(self, obj):
        return self.get_encrypted_file_display(obj, "passport")

    @admin.display(description="Signature")
    def get_signature_display(self, obj):
        return self.get_encrypted_file_display(obj, "signature")


if settings.KRONOS_ENABLED:
    admin.site.register(LoadEventsFromKronosTask, LoadEventsFromKronosTaskAdmin)
    admin.site.register(
        LoadParticipantsFromKronosTask, LoadParticipantsFromKronosTaskAdmin
    )
    admin.site.register(
        LoadOrganizationsFromKronosTask, LoadOrganizationsFromKronosTaskAdmin
    )
