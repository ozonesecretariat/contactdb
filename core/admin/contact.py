from functools import cached_property

from admin_auto_filters.filters import AutocompleteFilterFactory
from auditlog.models import LogEntry
from django import forms
from django.contrib import admin, messages
from django.contrib.admin.widgets import AutocompleteSelect
from django.db.models import BooleanField, Case, Count, Value, When
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe
from import_export import fields
from import_export.admin import ImportExportMixin
from import_export.widgets import ForeignKeyWidget
from more_admin_filters import BooleanAnnotationFilter

from common import fuzzy_search
from common.audit import bulk_audit_update
from common.auto_complete_multiple import AutocompleteFilterMultipleFactory
from common.import_export import ManyToManyWidgetWithCreation
from common.model_admin import ModelResource
from common.urls import reverse
from core.admin.contact_base import ContactAdminBase, MergeContacts
from core.models import (
    Contact,
    ContactGroup,
    Country,
    ImportContactPhotosTask,
    Organization,
)
from events.models import Registration


class OrganizationWidget(ForeignKeyWidget):
    def __init__(self):
        super().__init__(Organization, field="name")

    def clean(self, value, row=None, **kwargs):
        country = None
        if country_code := row.get("country"):
            country = Country.objects.get(code=country_code)
        return fuzzy_search.get_organization(value, country, country)


class ContactResource(ModelResource):
    organization = fields.Field(
        column_name="organization",
        attribute="organization",
        widget=OrganizationWidget(),
    )
    groups = fields.Field(
        column_name="groups",
        attribute="groups",
        widget=ManyToManyWidgetWithCreation(ContactGroup, field="name", create=True),
    )
    prefetch_related = (
        "organization",
        "country",
        "groups",
    )

    def skip_row(self, instance, original, row, import_validation_errors=None):
        if all(not i for i in row.values()):
            return True
        return super().skip_row(
            instance, original, row, import_validation_errors=import_validation_errors
        )

    class Meta:
        model = Contact
        exclude = (
            "id",
            "contact_id",
            "created_at",
            "updated_at",
            "contact_ids",
            "focal_point_ids",
        )
        import_id_fields = ()


class ContactMembershipInline(admin.StackedInline):
    extra = 0
    model = Contact.groups.through
    autocomplete_fields = ("contactgroup",)
    verbose_name = "Contact group"
    verbose_name_ = "Contact groups"

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("contactgroup")


class ContactRegistrationsInline(admin.StackedInline):
    extra = 0
    max_num = 0
    can_delete = 0
    model = Registration
    autocomplete_fields = ("event", "role", "tags", "organization")
    classes = ["collapse"]
    readonly_fields = ("event", "priority_pass")
    fieldsets = (
        (
            None,
            {"fields": (("event", "status"),)},
        ),
        (
            "More information",
            {
                "fields": (
                    "date",
                    "role",
                    ("priority_pass", "is_funded", "tags"),
                    ("organization", "designation", "department"),
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        return queryset.select_related(
            "contact",
            "event",
            "role",
            "organization",
            "organization__country",
            "organization__government",
        ).prefetch_related("tags")


@admin.register(Contact)
class ContactAdmin(MergeContacts, ImportExportMixin, ContactAdminBase):
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        for formset in formsets:
            # M2M logging doesn't work in inline models, so create them manually here.
            # See upstream: https://github.com/jazzband/django-auditlog/issues/638
            if formset.model == Contact.groups.through:
                LogEntry.objects.log_m2m_changes(
                    [obj.contactgroup for obj in formset.deleted_objects],
                    formset.instance,
                    "delete",
                    "groups",
                )
                LogEntry.objects.log_m2m_changes(
                    [obj.contactgroup for obj in formset.new_objects],
                    formset.instance,
                    "add",
                    "groups",
                )

    resource_class = ContactResource
    inlines = (
        ContactMembershipInline,
        ContactRegistrationsInline,
    )
    list_display = (
        "get_first_name",
        "get_last_name",
        "organization_link",
        "country",
        "emails",
        "primary",
        "secondary",
        "registrations_link",
        "email_logs",
        "id",
    )
    list_display_links = (
        "get_first_name",
        "get_last_name",
    )
    list_filter = (
        AutocompleteFilterMultipleFactory("country", "country"),
        AutocompleteFilterMultipleFactory("groups", "groups"),
        AutocompleteFilterMultipleFactory("organization", "organization"),
        AutocompleteFilterMultipleFactory("government", "organization__government"),
        AutocompleteFilterMultipleFactory(
            "organization type", "organization__organization_type"
        ),
        AutocompleteFilterFactory("event", "registrations__event"),
        "org_head",
        BooleanAnnotationFilter.init("primary"),
        BooleanAnnotationFilter.init("secondary"),
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "title_localized",
                    "honorific",
                    "first_name",
                    "last_name",
                    "photo",
                ),
            },
        ),
        (
            "Contact info",
            {
                "fields": (
                    "emails",
                    "email_ccs",
                    "phones",
                    "mobiles",
                    "faxes",
                )
            },
        ),
        (
            "Organization",
            {
                "fields": (
                    "organization",
                    "designation",
                    "department",
                    "org_head",
                )
            },
        ),
        (
            "Address",
            {
                "classes": ["collapse"],
                "fields": (
                    "is_use_organization_address",
                    ("country", "city"),
                    ("state", "postal_code"),
                    "address",
                ),
            },
        ),
        (
            "Credentials",
            {
                "classes": ["collapse"],
                "fields": (
                    "has_credentials",
                    "credentials_display",
                ),
            },
        ),
        (
            "Passport",
            {
                "classes": ["collapse"],
                "fields": (
                    "needs_visa_letter",
                    "passport_number",
                    "nationality",
                    "passport_date_of_issue",
                    "passport_date_of_expiry",
                    "passport_display",
                ),
            },
        ),
        (
            "Language",
            {
                "classes": ["collapse"],
                "fields": (
                    "primary_lang",
                    "second_lang",
                    "third_lang",
                ),
            },
        ),
        (
            "Personal information",
            {
                "classes": ["collapse"],
                "fields": (
                    "birth_date",
                    "gender",
                    "notes",
                ),
            },
        ),
        (
            "Metadata",
            {
                "classes": ["collapse"],
                "fields": (
                    "contact_ids",
                    "focal_point_ids",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
        (
            "Emails",
            {
                "classes": ["collapse"],
                "fields": ("email_links",),
            },
        ),
    )
    readonly_fields = ContactAdminBase.readonly_fields + (
        "contact_ids",
        "focal_point_ids",
        "email_links",
        "passport_display",
        "credentials_display",
        "has_credentials",
    )
    annotate_query = {
        "registration_count": Count("registrations"),
        "primary": Case(
            When(primary_for_orgs__isnull=False, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        "secondary": Case(
            When(secondary_for_orgs__isnull=False, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
    }
    actions = [
        "send_email",
        "add_contacts_to_group",
        "merge_contacts",
        "import_photos_from_kronos",
    ]

    @admin.display(description="Events", ordering="registration_count")
    def registrations_link(self, obj):
        return self.get_related_link(
            obj,
            "registrations",
            "contact",
            f"{obj.registration_count} events",
        )

    @admin.display(ordering="primary", boolean=True)
    def primary(self, obj):
        return obj.primary

    @admin.display(ordering="secondary", boolean=True)
    def secondary(self, obj):
        return obj.secondary

    @admin.display(description="Emails", ordering="-email_tasks")
    def email_links(self, obj):
        return self.get_m2m_links(obj.email_logs.all())

    @admin.action(description="Merge selected contacts", permissions=["change"])
    def merge_contacts(self, request, queryset):
        return self.merge_action(request, queryset)

    @admin.action(description="Add selected contacts to group", permissions=["change"])
    def add_contacts_to_group(self, request, queryset):
        if "apply" in request.POST:
            group = get_object_or_404(ContactGroup, pk=request.POST["group"])
            group_str = smart_str(group)
            memberships = []
            for contact in queryset:
                memberships.append(
                    Contact.groups.through(contactgroup=group, contact=contact)
                )
            Contact.groups.through.objects.bulk_create(
                memberships, batch_size=1000, ignore_conflicts=True
            )
            bulk_audit_update(
                queryset,
                {
                    "groups": {
                        "type": "m2m",
                        "operation": "add",
                        "objects": [group_str],
                    }
                },
                request=request,
            )
            self.message_user(
                request,
                f"{len(memberships)} contacts added to {group!r}",
                messages.SUCCESS,
            )
            return None

        widget = AutocompleteSelect(
            Contact.groups.through._meta.get_field("contactgroup"),
            admin_site=self.admin_site,
            attrs={
                "id": "select-contactgroup",
            },
        )
        field = forms.ModelChoiceField(
            queryset=ContactGroup.objects.all(), widget=widget
        )

        return self.get_intermediate_response(
            "admin/actions/add_contacts_to_group.html",
            request,
            queryset,
            {
                "media": widget.media,
                "widget": field.widget.render("group", None),
                "title": "Please select group",
            },
        )

    @admin.action(description="Import photos from Kronos", permissions=["change"])
    def import_photos_from_kronos(self, request, queryset):
        """Import photos for selected contacts from Kronos API."""
        if "apply" in request.POST:
            overwrite = request.POST.get("overwrite", "on") == "on"

            contact_ids = list(queryset.values_list("id", flat=True))

            task = ImportContactPhotosTask.objects.create(
                overwrite_existing=overwrite,
                contact_ids=contact_ids,
            )
            task.run(is_async=True)

            self.message_user(
                request,
                f"Photo import task {task.id} started for {len(contact_ids)} contact(s)",
                messages.SUCCESS,
            )
            return None

        return self.get_intermediate_response(
            "admin/actions/import_contact_photos.html",
            request,
            queryset,
            {
                "title": "Import Contact Photos from Kronos",
            },
        )

    @admin.action(description="Send email to selected contacts", permissions=["view"])
    def send_email(self, request, queryset):
        ids = ",".join(map(str, queryset.values_list("id", flat=True)))
        return redirect(reverse("admin:emails_email_add") + "?recipients=" + ids)

    @cached_property
    def empty_value(self):
        return mark_safe("<i>(empty)</i>")

    @admin.display(description="First name", ordering="first_name")
    def get_first_name(self, obj):
        return obj.first_name or self.empty_value

    @admin.display(description="Last name", ordering="last_name")
    def get_last_name(self, obj):
        return obj.last_name or self.empty_value

    @admin.display(description="Organization", ordering="organization")
    def organization_link(self, obj):
        return self.get_object_display_link(obj.organization)

    def _get_file_display(self, obj, field):
        if not (file := getattr(obj, field)):
            return "-"

        try:
            b64data = file["data"]
            filename = file["filename"]
        except KeyError:
            return "-"

        return mark_safe(f'<a href="data:{b64data}" download="{filename}">Download</a>')

    @admin.display(description="Credentials")
    def credentials_display(self, obj):
        return self._get_file_display(obj, "credentials")

    @admin.display(description="Passport")
    def passport_display(self, obj):
        return self._get_file_display(obj, "passport")
