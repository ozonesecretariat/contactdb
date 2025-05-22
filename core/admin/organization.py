from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.db.models import Count
from import_export.admin import ExportMixin

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
    ]
    filter_horizontal = ("primary_contacts", "secondary_contacts")
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
        "include_in_invitation",
    )
    readonly_fields = ("organization_id",)
    autocomplete_fields = ("country", "government", "organization_type")
    prefetch_related = ("country", "government", "organization_type")
    annotate_query = {
        "contacts_count": Count("contacts"),
    }

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name in ["primary_contacts", "secondary_contacts"]:
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
