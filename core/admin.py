from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages
from django.contrib.admin import EmptyFieldListFilter, helpers
from django.contrib.admin.utils import flatten_fieldsets
from django.contrib.admin.widgets import AutocompleteSelect
from django import forms
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.html import format_html
from import_export import fields
from import_export.admin import ImportExportMixin
from import_export.widgets import ForeignKeyWidget

from common.urls import reverse
from common.model_admin import ModelAdmin, TaskAdmin, ModelResource
from core.jobs import ResolveAllConflicts

from core.models import (
    Country,
    GroupMembership,
    Organization,
    Contact,
    ContactGroup,
    OrganizationType,
    ResolveAllConflictsTask,
    ResolveConflict,
)

MERGE_FROM_PARAM = "merge_from_temp"


@admin.register(ResolveAllConflictsTask)
class ResolveAllConflictsTaskAdmin(TaskAdmin):
    list_display = [
        "__str__",
        "created_on",
        "duration_display",
        "status_display",
    ]
    ordering = ("-created_on",)


@admin.register(Country)
class CountryAdmin(ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
    list_display_links = ("code", "name")


@admin.register(OrganizationType)
class OrganizationTypeAdmin(ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)
    readonly_fields = ("organization_type_id",)


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    search_fields = [
        "name",
        "acronym",
        "organization_type__name",
        "government__name",
        "country__name",
    ]
    list_filter = (
        AutocompleteFilterFactory("organization_type", "organization_type"),
        AutocompleteFilterFactory("country", "country"),
        AutocompleteFilterFactory("government", "government"),
    )
    list_display = (
        "name",
        "acronym",
        "organization_type",
        "country",
        "government",
        "contacts_count",
    )
    readonly_fields = ("organization_id",)
    autocomplete_fields = ("country", "government", "organization_type")
    prefetch_related = ("country", "government", "organization_type")
    annotate_query = {
        "contacts_count": Count("contacts"),
    }

    @admin.display(description="Contacts", ordering="contacts_count")
    def contacts_count(self, obj):
        return self.get_related_link(
            obj, "contacts", "organization", obj.contacts_count
        )


class ContactResource(ModelResource):
    organization = fields.Field(
        column_name="organization",
        attribute="organization",
        widget=ForeignKeyWidget(Organization, "name"),
    )
    prefetch_related = ("organization", "main_contact", "country")

    class Meta:
        model = Contact
        exclude = (
            "id",
            "contact_id",
            "main_contact",
            "created_at",
            "updated_at",
        )
        import_id_fields = ("emails",)


class ContactAdminBase(ModelAdmin):
    ordering = (
        "first_name",
        "last_name",
    )
    search_fields = (
        "contact_id",
        "first_name",
        "last_name",
        "designation",
        "department",
        "emails",
        "organization__name",
    )
    list_display = (
        "title",
        "first_name",
        "last_name",
        "organization",
        "country",
        "emails",
        "phones",
        "sent_emails",
    )
    list_display_links = (
        "first_name",
        "last_name",
    )
    autocomplete_fields = (
        "organization",
        "country",
        "main_contact",
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
                    ("is_in_mailing_list", "focal_point"),
                ),
            },
        ),
        (
            "Contact info",
            {
                "fields": (
                    "main_contact",
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
                    "contact_id",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )
    readonly_fields = (
        "contact_id",
        "created_at",
        "updated_at",
        "copy_widget",
    )

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        if MERGE_FROM_PARAM in request.GET:
            extra_context["title"] = "Resolve contact conflict"

        return super().change_view(
            request,
            object_id,
            form_url=form_url,
            extra_context=extra_context,
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if temp_contact_pk := request.GET.get(MERGE_FROM_PARAM):
            get_object_or_404(ResolveConflict, pk=temp_contact_pk).delete()

    def get_queryset(self, request):
        query = super().get_queryset(request)
        if temp_contact_pk := request.GET.get(MERGE_FROM_PARAM):
            query = query.prefetch_related(
                Prefetch(
                    "conflicting_contacts",
                    ResolveConflict.objects.filter(pk=temp_contact_pk)[:1],
                    to_attr="incoming_contact",
                )
            )
        return query

    def get_readonly_fields(self, request, obj=None):
        result = super().get_readonly_fields(request, obj=obj)
        if not obj or MERGE_FROM_PARAM not in request.GET:
            return result

        return result + tuple(
            [
                "incoming_contact__" + field
                for field in flatten_fieldsets(self.get_fieldsets(request, obj))
            ]
        )

    def copy_widget(self, obj):
        return format_html(
            '<input type="button" class="copy-button" title="Copy value" value="←" />'
        )

    def __getattr__(self, name):
        if not name.startswith("incoming_contact__"):
            return super().__getattribute__(name)

        field_name = name.split("__", 1)[1]

        def wrapper(obj):
            value = getattr(obj.incoming_contact[0], field_name)
            if isinstance(value, list):
                return render_to_string(
                    "admin/widgets/array_widget_readonly.html",
                    {
                        "value": value,
                    },
                )

            if hasattr(value, "pk"):
                return format_html(
                    "<span data-pk={pk}>{value}</span>", pk=value.pk, value=value
                )

            if value is None or value == "":
                return self.get_empty_value_display()

            return value

        wrapper.short_description = field_name.replace("_", " ").title()

        return wrapper

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj=obj)
        if not obj or MERGE_FROM_PARAM not in request.GET:
            return fieldsets

        result = []
        for name, opts in fieldsets:
            # Flatten fieldset and add the copy widget and the incoming contact
            # readonly fields.
            fields = []
            for field_group in opts["fields"]:
                if not isinstance(field_group, tuple):
                    field_group = (field_group,)

                for field in field_group:
                    if field in self.readonly_fields:
                        continue
                    fields.append((field, "copy_widget", "incoming_contact__" + field))

            if not fields:
                continue

            result.append(
                (
                    name,
                    {
                        **opts,
                        "classes": ["compare"],
                        "fields": fields,
                    },
                )
            )
        return result

    def get_inlines(self, request, obj):
        if MERGE_FROM_PARAM in request.GET:
            return ()
        return super().get_inlines(request, obj)

    @admin.display(description="Sent emails")
    def sent_emails(self, obj):
        return self.get_related_link(obj, "email_history", "contact")


class ContactMembershipInline(admin.StackedInline):
    fields = ("group",)
    extra = 0
    model = GroupMembership
    autocomplete_fields = ("group",)
    verbose_name = "Group Contact"
    verbose_name_ = "Group Contacts"


@admin.register(Contact)
class ContactAdmin(ImportExportMixin, ContactAdminBase):
    resource_class = ContactResource
    inlines = (ContactMembershipInline,)

    list_filter = (
        ("main_contact", EmptyFieldListFilter),
        AutocompleteFilterFactory("organization", "organization"),
        AutocompleteFilterFactory("country", "country"),
        AutocompleteFilterFactory("event", "registrations__event"),
        AutocompleteFilterFactory("group", "memberships__group"),
        "org_head",
        "is_in_mailing_list",
        "is_use_organization_address",
        "focal_point",
    )
    prefetch_related = (
        "organization",
        "main_contact",
        "country",
    )
    actions = ["add_contacts_to_group", "merge_contacts"]

    @admin.action(description="Merge contacts", permissions=["change"])
    def merge_contacts(self, request, queryset):
        if "apply" in request.POST:
            main_contact = get_object_or_404(Contact, pk=request.POST["main_contact"])
            secondary_contacts = queryset.exclude(pk=main_contact.pk)

            Contact.objects.filter(main_contact__in=secondary_contacts).update(
                main_contact=main_contact
            )
            secondary_contacts.update(main_contact=main_contact)
            self.message_user(
                request,
                f"{queryset.count()} merged into {main_contact!r}",
                messages.SUCCESS,
            )
            return

        return self.get_intermediate_response(
            "admin/actions/merge_contacts.html",
            request,
            queryset,
            {
                "title": "Please select main contact",
            },
        )

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


@admin.register(ResolveConflict)
class ResolveConflictAdmin(ContactAdminBase):
    list_filter = (
        ("main_contact", EmptyFieldListFilter),
        AutocompleteFilterFactory("organization", "organization"),
        AutocompleteFilterFactory("country", "country"),
        "org_head",
        "is_in_mailing_list",
        "is_use_organization_address",
        "focal_point",
    )
    list_display = (
        "existing_contact_link",
        "new_contact",
    )
    list_display_links = ()
    prefetch_related = ("existing_contact",)
    actions = ("accept_new_data",)

    @admin.action(
        description="Accept new data for selected conflicts", permissions=["delete"]
    )
    def accept_new_data(self, request, queryset):
        new_contacts = list(queryset)
        for temp_contact in new_contacts:
            ResolveAllConflicts.save_incoming_data(temp_contact)

        self.message_user(
            request,
            f"{len(new_contacts)} conflicts resolved",
            messages.SUCCESS,
        )

    @admin.display(description="Existing contact")
    def existing_contact_link(self, obj):
        next_url = reverse("admin:core_resolveconflict_changelist")
        url = reverse(
            "admin:core_contact_change",
            kwargs={"object_id": obj.existing_contact.id},
            query={
                MERGE_FROM_PARAM: obj.pk,
                self.redirect_field_name: next_url,
            },
        )
        return format_html(
            '<a href="{url}">{name}</a>', url=url, name=obj.existing_contact
        )

    @admin.display(description="New contact")
    def new_contact(self, obj):
        return str(obj)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ContactGroup)
class ContactGroupAdmin(ModelAdmin):
    search_fields = ("name", "description")
    list_display = (
        "name",
        "description_preview",
        "contacts_count",
    )
    exclude = ("contacts",)
    prefetch_related = ("contacts",)
    annotate_query = {
        "contacts_count": Count("contacts"),
    }

    @admin.display(description="Contacts", ordering="contacts_count")
    def contacts_count(self, obj):
        return self.get_related_link(
            obj, "contacts", "memberships__group", obj.contacts_count
        )
