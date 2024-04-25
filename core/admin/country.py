from django.contrib import admin
from common.model_admin import ModelAdmin
from core.models import Country


@admin.register(Country)
class CountryAdmin(ModelAdmin):
    list_display = ("code", "name", "official_name")
    search_fields = ("code", "name", "official_name")
    list_display_links = ("code", "name", "official_name")
