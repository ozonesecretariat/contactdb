from django.contrib import admin
from import_export.admin import ExportMixin

from common.model_admin import ModelAdmin
from core.models import Region, Subregion


@admin.register(Region)
class RegionAdmin(ExportMixin, ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name__unaccent")
    list_display_links = ("code", "name")


@admin.register(Subregion)
class SubregionAdmin(ExportMixin, ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name__unaccent")
    list_display_links = ("code", "name")
