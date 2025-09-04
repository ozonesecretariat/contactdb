from django.contrib import admin
from import_export.admin import ExportMixin

from common.model_admin import ModelAdmin
from core.models import OrganizationType


@admin.register(OrganizationType)
class OrganizationTypeAdmin(ExportMixin, ModelAdmin):
    search_fields = (
        "acronym",
        "title",
        "description",
        "badge_title",
        "statistics_title",
    )
    list_display = (
        "acronym",
        "title",
        "badge_color",
        "badge_title",
        "statistics_title",
        "description",
        "hide_in_lop",
        "hide_in_statistics",
        "sort_order",
    )
    readonly_fields = ("organization_type_id",)
