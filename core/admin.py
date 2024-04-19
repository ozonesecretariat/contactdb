from copy import copy
from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages
from django.contrib.admin import EmptyFieldListFilter, helpers
from django.contrib.admin.utils import flatten_fieldsets
from django.contrib.admin.widgets import AutocompleteSelect
from django import forms
from django.db import IntegrityError, models
from django.db.models import Count, ManyToManyRel, ManyToOneRel, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.html import format_html
from import_export import fields
from import_export.admin import ImportExportMixin
from import_export.widgets import ForeignKeyWidget
from common.array_field import ArrayField

from common.urls import reverse
from common.model_admin import ModelAdmin, TaskAdmin, ModelResource
from common.utils import update_object

from core.models import (
    Country,
    GroupMembership,
    Organization,
    Contact,
    ContactGroup,
    OrganizationType,
    ResolveConflict,
)
from events.models import Registration

MERGE_FROM_PARAM = "merge_from_temp"


@admin.register(Country)
class CountryAdmin(ModelAdmin):
    list_display = ("code", "name", "official_name")
    search_fields = ("code", "name", "official_name")
    list_display_links = ("code", "name", "official_name")


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
            obj,
            "contacts",
            "organization",
            f"{obj.contacts_count} contacts",
        )


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


class ContactAdminBase(ModelAdmin):
    ordering = (
        "first_name",
        "last_name",
    )
    search_fields = (
        "first_name",
        "last_name",
        "designation",
        "department",
        "emails",
        "organization__name",
        "organization__country__name",
    )
    autocomplete_fields = (
        "organization",
        "country",
    )
    prefetch_related = (
        "organization",
        "organization__country",
        "country",
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
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )
    readonly_fields = (
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
    def email_logs(self, obj):
        return self.get_related_link(obj, "email_logs", "contact")


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
class ContactAdmin(ImportExportMixin, ContactAdminBase):
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
        "focal_point",
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

    def merge_two_contacts(self, contact1, contact2):
        ignored_fields = {
            "id",
            "contact_id",
            "created_at",
            "updated_at",
            "memberships",  # Through model, already cover by groups; can be ignored
            "conflicting_contacts",
        }

        has_conflict = False
        for field in self.opts.get_fields():
            if field.is_relation and getattr(field, "multiple", False):
                assert field.related_name, f"Missing related name: {field}"
                name = field.related_name
            else:
                name = field.name

            if name in ignored_fields:
                continue

            val1 = getattr(contact1, name)
            val2 = getattr(contact2, name)

            val1_empty = val1 == "" or val1 is None
            val2_empty = val2 == "" or val2 is None

            if isinstance(field, ManyToManyRel):
                for item in val2.all():
                    val1.add(item)
            elif isinstance(field, ManyToOneRel):
                rel_name = field.field.name
                for item in val2.all():
                    try:
                        setattr(item, rel_name, contact1)
                        item.save()
                    except IntegrityError:
                        continue
            elif isinstance(field, models.BooleanField):
                if val1 != val2:
                    has_conflict = True
            elif isinstance(field, ArrayField):
                if val1 is None:
                    setattr(contact1, name, [])
                    val1 = getattr(contact1, name)

                for item in val2 or []:
                    if item not in val1:
                        val1.append(item)

                setattr(contact2, name, [])
            elif isinstance(
                field,
                (
                    models.CharField,
                    models.TextField,
                    models.IntegerField,
                    models.FloatField,
                    models.DecimalField,
                    models.DateField,
                    models.ForeignKey,
                ),
            ):
                if val1 == val2:
                    # Values are equal nothing to do
                    continue
                elif val1_empty and val2_empty:
                    # Values are empty but different (e.g. "" vs None).
                    # No conflict.
                    continue
                elif val1_empty or val2_empty:
                    # Only one value is empty, use the non-empty one
                    setattr(contact1, name, val1 or val2)
                else:
                    # Values differ
                    has_conflict = True
            else:
                raise RuntimeError(f"Unexpected field type: {field}")
        contact1.save()
        contact2.save()

        return has_conflict

    @admin.action(description="Merge selected contacts", permissions=["change"])
    def merge_contacts(self, request, queryset):
        all_contacts = list(queryset)
        if len(all_contacts) < 2:
            self.message_user(
                request,
                "Need at least 2 contacts to merge.",
                messages.ERROR,
            )
            return

        conflicts = []
        main_contact = all_contacts[0]
        for other_contact in all_contacts[1:]:
            if self.merge_two_contacts(main_contact, other_contact):
                conflicts.append(
                    ResolveConflict.create_from_contact(main_contact, other_contact)
                )
            other_contact.delete()

        if not conflicts:
            self.message_user(
                request,
                f"{len(all_contacts)} merged successfully.",
                messages.SUCCESS,
            )
        elif len(conflicts) == 1:
            self.message_user(
                request,
                (
                    f"One contact could not be merged automatically. "
                    f"Please resolve the conflicts manually and click save."
                ),
                messages.WARNING,
            )
            return redirect(
                reverse(
                    "admin:core_contact_change",
                    kwargs={"object_id": main_contact.id},
                    query={
                        MERGE_FROM_PARAM: conflicts[0].id,
                    },
                )
            )
        else:
            self.message_user(
                request,
                (
                    f"{len(conflicts)} contacts could not be merged automatically. "
                    f"Please click below to resolve each conflict manually."
                ),
                messages.WARNING,
            )
            return redirect(
                self.get_admin_list_link(ResolveConflict, {"contact": main_contact.id})
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

    @admin.action(description="Send email to selected contacts", permissions=["view"])
    def send_email(self, request, queryset):
        ids = ",".join(map(str, queryset.values_list("id", flat=True)))
        return redirect(reverse("admin:emails_email_add") + "?recipients=" + ids)


@admin.register(ResolveConflict)
class ResolveConflictAdmin(ContactAdminBase):
    search_fields = (
        "first_name",
        "last_name",
        "designation",
        "department",
        "emails",
        "organization__name",
        "organization__country__name",
        "existing_contact__first_name",
        "existing_contact__last_name",
        "existing_contact__designation",
        "existing_contact__department",
        "existing_contact__emails",
        "existing_contact__organization__name",
        "existing_contact__organization__country__name",
    )
    list_filter = (
        AutocompleteFilterFactory("organization", "organization"),
        AutocompleteFilterFactory("country", "country"),
        "org_head",
        "is_in_mailing_list",
        "is_use_organization_address",
        "focal_point",
    )
    list_display = (
        "existing_contact_link",
        "conflicting_contact",
    )
    list_display_links = (
        "existing_contact_link",
        "conflicting_contact",
    )
    prefetch_related = (
        "organization",
        "organization__country",
        "existing_contact",
        "existing_contact__organization",
        "existing_contact__organization__country",
    )
    actions = ("accept_new_data",)

    @admin.action(
        description="Accept new data for selected conflicts", permissions=["delete"]
    )
    def accept_new_data(self, request, queryset):
        new_contacts = list(queryset)
        for temp_contact in new_contacts:
            self.save_incoming_data(temp_contact)

        self.message_user(
            request,
            f"{len(new_contacts)} conflicts resolved",
            messages.SUCCESS,
        )

    @staticmethod
    def save_incoming_data(incoming_contact):
        record = incoming_contact.existing_contact
        update_values = copy(dict(vars(incoming_contact)))
        update_values.pop("existing_contact_id")
        update_values.pop("id")
        update_object(record, update_values)
        for key, value in update_values.items():
            setattr(record, key, value)
        record.save()
        ResolveConflict.objects.filter(pk=incoming_contact.id).first().delete()

    def _link_to_conflict_resolution(self, obj, text):
        next_url = reverse("admin:core_resolveconflict_changelist")
        url = reverse(
            "admin:core_contact_change",
            kwargs={"object_id": obj.existing_contact.id},
            query={
                MERGE_FROM_PARAM: obj.pk,
                self.redirect_field_name: next_url,
            },
        )
        return format_html('<a href="{url}">{text}</a>', url=url, text=text)

    @admin.display(description="Existing contact")
    def existing_contact_link(self, obj):
        return self._link_to_conflict_resolution(obj, obj.existing_contact)

    @admin.display(description="Conflicting contact")
    def conflicting_contact(self, obj):
        return self._link_to_conflict_resolution(obj, obj)

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
    actions = ("send_email",)

    @admin.display(description="Contacts", ordering="contacts_count")
    def contacts_count(self, obj):
        return self.get_related_link(
            obj, "contacts", "memberships__group", obj.contacts_count
        )

    @admin.action(description="Send email to selected groups", permissions=["view"])
    def send_email(self, request, queryset):
        ids = ",".join(map(str, queryset.values_list("id", flat=True)))
        return redirect(reverse("admin:emails_email_add") + "?groups=" + ids)
