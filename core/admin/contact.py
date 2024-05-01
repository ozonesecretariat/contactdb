from admin_auto_filters.filters import AutocompleteFilterFactory
from auditlog.models import LogEntry
from django import forms
from django.contrib import admin, messages
from django.contrib.admin.widgets import AutocompleteSelect
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import smart_str
from import_export import fields
from import_export.admin import ImportExportMixin
from import_export.widgets import ForeignKeyWidget
from common.audit import bulk_audit_update
from common.model_admin import ModelResource
from common.urls import reverse
from core.admin.contact_base import ContactAdminBase, MergeContacts
from core.models import Contact, ContactGroup, Organization
from events.models import Registration


class ContactResource(ModelResource):
    organization = fields.Field(
        column_name="organization",
        attribute="organization",
        widget=ForeignKeyWidget(Organization, "name"),
    )
    prefetch_related = ("organization", "country")

    class Meta:
        model = Contact
        exclude = (
            "id",
            "contact_id",
            "created_at",
            "updated_at",
        )
        import_id_fields = ("emails",)


class ContactMembershipInline(admin.StackedInline):
    extra = 0
    model = Contact.groups.through
    autocomplete_fields = ("contactgroup",)
    verbose_name = "Group Contact"
    verbose_name_ = "Group Contacts"

    def has_change_permission(self, request, obj=None):
        return False


class ContactRegistrationsInline(admin.StackedInline):
    extra = 0
    model = Registration
    autocomplete_fields = ("event", "status", "role", "tags")


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
        "title",
        "first_name",
        "last_name",
        "organization",
        "country",
        "emails",
        "phones",
        "registrations_link",
        "email_logs",
    )
    list_display_links = (
        "first_name",
        "last_name",
    )
    list_filter = (
        AutocompleteFilterFactory("organization", "organization"),
        AutocompleteFilterFactory("country", "country"),
        AutocompleteFilterFactory("event", "registrations__event"),
        "groups",
        "org_head",
        "is_in_mailing_list",
        "is_use_organization_address",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("title", "honorific", "respectful"),
                    "first_name",
                    "last_name",
                    "country",
                    "is_in_mailing_list",
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
                    "affiliation",
                    "org_head",
                    "is_use_organization_address",
                )
            },
        ),
        (
            "Address",
            {
                "classes": ["collapse"],
                "fields": (
                    ("city", "state", "postal_code"),
                    "address",
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
            "Other",
            {
                "classes": ["collapse"],
                "fields": (
                    "birth_date",
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
    )
    readonly_fields = ContactAdminBase.readonly_fields + (
        "contact_ids",
        "focal_point_ids",
    )
    annotate_query = {
        "registration_count": Count("registrations"),
    }
    actions = [
        "send_email",
        "add_contacts_to_group",
        "merge_contacts",
    ]

    @admin.display(description="Events", ordering="registration_count")
    def registrations_link(self, obj):
        return self.get_related_link(
            obj,
            "registrations",
            "contact",
            f"{obj.registration_count} registrations",
        )

    @admin.action(description="Merge selected contacts", permissions=["change"])
    def merge_contacts(self, request, queryset):
        return self.merge_action(request, queryset)

    @admin.action(description="Add selected contacts to group", permissions=["change"])
    def add_contacts_to_group(self, request, queryset):
        if "apply" in request.POST:
            group = get_object_or_404(ContactGroup, pk=request.POST["group"])
            group_str = smart_str(group)
            memberships = []
            log_entries = []
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
            return

        widget = AutocompleteSelect(
            Contact.groups.through._meta.get_field("contactgroup"),
            admin_site=self.admin_site,
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

    @admin.action(description="Send email to selected contacts", permissions=["view"])
    def send_email(self, request, queryset):
        ids = ",".join(map(str, queryset.values_list("id", flat=True)))
        return redirect(reverse("admin:emails_email_add") + "?recipients=" + ids)
