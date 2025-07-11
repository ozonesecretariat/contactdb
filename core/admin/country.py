from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from import_export.admin import ExportMixin

from common.model_admin import ModelAdmin
from core.models import Country


@admin.register(Country)
class CountryAdmin(ExportMixin, ModelAdmin):
    list_display = ("code", "name", "official_name", "region", "subregion")
    search_fields = (
        "code",
        "name__unaccent",
        "official_name__unaccent",
    )
    list_display_links = ("code", "name", "official_name")
    list_filter = (
        AutocompleteFilterFactory("region", "region"),
        AutocompleteFilterFactory("subregion", "subregion"),
    )
    prefetch_related = ("region", "subregion")
