from django.contrib import admin
from import_export.admin import ExportMixin
from common.model_admin import ModelAdmin
from core.models import OrganizationType


@admin.register(OrganizationType)
class OrganizationTypeAdmin(ExportMixin, ModelAdmin):
    search_fields = ("acronym", "title", "description")
    list_display = ("acronym", "title", "description")
    readonly_fields = ("organization_type_id",)
