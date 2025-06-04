from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.db.models import BooleanField, Case, Count, Value, When
from import_export.admin import ExportMixin
from more_admin_filters import BooleanAnnotationFilter

from common.auto_complete_multiple import AutocompleteFilterMultipleFactory
from common.model_admin import ModelAdmin
from core.models import Organization


@admin.register(Organization)
class OrganizationAdmin(ExportMixin, ModelAdmin):
    search_fields = [
        "name__unaccent",
        "acronym",
        "organization_type__acronym",
        "organization_type__title",
        "organization_type__description",
        "government__name__unaccent",
        "country__name__unaccent",
        "emails",
        "email_ccs",
    ]
    filter_horizontal = ("primary_contacts", "secondary_contacts")
    list_filter = (
        AutocompleteFilterMultipleFactory("organization type", "organization_type"),
        AutocompleteFilterFactory("country", "country"),
        AutocompleteFilterFactory("government", "government"),
        "include_in_invitation",
        BooleanAnnotationFilter.init("has_primary_contacts"),
        BooleanAnnotationFilter.init("has_secondary_contacts"),
    )
    list_display = (
        "name",
        "organization_type",
        "country",
        "government",
        "emails",
        "has_primary_contacts",
        "has_secondary_contacts",
        "include_in_invitation",
        "contacts_count",
        "id",
    )
    readonly_fields = (
        "organization_id",
        "email_links",
    )
    autocomplete_fields = ("country", "government", "organization_type")
    prefetch_related = ("country", "government", "organization_type")
    annotate_query = {
        "contacts_count": Count("contacts", distinct=True),
        "has_primary_contacts": Case(
            When(primary_contacts__gt=0, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        "has_secondary_contacts": Case(
            When(secondary_contacts__gt=0, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
    }
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "acronym",
                    "organization_type",
                    "government",
                    "include_in_invitation",
                )
            },
        ),
        (
            "Contacts",
            {
                "fields": (
                    "primary_contacts",
                    "secondary_contacts",
                )
            },
        ),
        (
            "Contact info",
            {
                "fields": (
                    "phones",
                    "faxes",
                    "websites",
                    "emails",
                    "email_ccs",
                )
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "country",
                    ("city", "state", "postal_code"),
                    "address",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("organization_id",),
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

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ["primary_contacts", "secondary_contacts"]:
            kwargs["required"] = False
            if "object_id" in request.resolver_match.kwargs:
                # Changing an existing organization - only displaying related contacts
                organization = self.get_object(
                    request, request.resolver_match.kwargs["object_id"]
                )
                if organization:
                    kwargs["queryset"] = organization.contacts.all()
            else:
                # Adding a new organization - no contacts will be displayed
                kwargs["queryset"] = db_field.remote_field.model.objects.none()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    @admin.display(description="Contacts", ordering="contacts_count")
    def contacts_count(self, obj):
        return self.get_related_link(
            obj,
            "contacts",
            "organization",
            f"{obj.contacts_count} contacts",
        )

    @admin.display(
        description="Primary contacts", ordering="primary_contacts", boolean=True
    )
    def has_primary_contacts(self, obj):
        return obj.primary_contacts.exists()

    @admin.display(
        description="Secondary contacts", ordering="secondary_contacts", boolean=True
    )
    def has_secondary_contacts(self, obj):
        return obj.secondary_contacts.exists()

    @admin.display(description="Emails", ordering="-email_tasks")
    def email_links(self, obj):
        return self.get_m2m_links(obj.email_tasks.all())
