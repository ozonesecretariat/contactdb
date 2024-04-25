from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.db.models import Count
from import_export.admin import ExportMixin
from common.model_admin import ModelAdmin
from core.models import Organization


@admin.register(Organization)
class OrganizationAdmin(ExportMixin, ModelAdmin):
    search_fields = [
        "name",
        "acronym",
        "organization_type__acronym",
        "organization_type__title",
        "organization_type__description",
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
