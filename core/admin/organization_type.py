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
        "protected",
    )
    readonly_fields = ("organization_type_id", "protected")

    def get_readonly_fields(self, request, obj=None):
        result = super().get_readonly_fields(request, obj)
        if not obj or not obj.protected:
            return result
        return tuple(result) + ("acronym",)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.protected:
            return False
        return super().has_delete_permission(request, obj)
