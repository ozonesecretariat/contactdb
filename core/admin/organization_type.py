from django.contrib import admin
from common.model_admin import ModelAdmin
from core.models import OrganizationType


@admin.register(OrganizationType)
class OrganizationTypeAdmin(ModelAdmin):
    search_fields = ("acronym", "title", "description")
    list_display = ("acronym", "title", "description")
    readonly_fields = ("organization_type_id",)
