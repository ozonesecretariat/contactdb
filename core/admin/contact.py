from admin_auto_filters.filters import AutocompleteFilterFactory
from django import forms
from django.contrib import admin, messages
from django.contrib.admin.widgets import AutocompleteSelect
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from import_export import fields
from import_export.admin import ImportExportMixin
from import_export.widgets import ForeignKeyWidget
from common.model_admin import ModelResource
from common.urls import reverse
from core.admin.contact_base import ContactAdminBase, MergeContacts
from core.models import Contact, ContactGroup, GroupMembership, Organization
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
    fields = ("group",)
    extra = 0
    model = GroupMembership
    autocomplete_fields = ("group",)
    verbose_name = "Group Contact"
    verbose_name_ = "Group Contacts"


class ContactRegistrationsInline(admin.StackedInline):
    extra = 0
    model = Registration
    autocomplete_fields = ("event", "status", "role", "tags")


@admin.register(Contact)
class ContactAdmin(MergeContacts, ImportExportMixin, ContactAdminBase):
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
        AutocompleteFilterFactory("group", "memberships__group"),
        "org_head",
        "is_in_mailing_list",
        "is_use_organization_address",
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
            memberships = []
            for contact in queryset:
                memberships.append(GroupMembership(group=group, contact=contact))
            GroupMembership.objects.bulk_create(
                memberships, batch_size=1000, ignore_conflicts=True
            )
            self.message_user(
                request,
                f"{len(memberships)} contacts added to {group!r}",
                messages.SUCCESS,
            )
            return

        widget = AutocompleteSelect(
            GroupMembership._meta.get_field("group"), admin_site=self.admin_site
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
