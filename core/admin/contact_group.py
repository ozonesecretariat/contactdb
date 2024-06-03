from django.contrib import admin
from django.db.models import Count
from django.shortcuts import redirect
from import_export.admin import ExportMixin
from common.model_admin import ModelAdmin
from common.urls import reverse
from core.models import ContactGroup


@admin.register(ContactGroup)
class ContactGroupAdmin(ExportMixin, ModelAdmin):
    search_fields = ("name__unaccent", "description__unaccent")
    list_display = (
        "name",
        "predefined",
        "description_preview",
        "contacts_count",
    )
    list_filter = ("predefined",)
    exclude = ("contacts",)
    prefetch_related = ("contacts",)
    annotate_query = {
        "contacts_count": Count("contacts"),
    }
    actions = ("send_email",)

    @admin.display(description="Contacts", ordering="contacts_count")
    def contacts_count(self, obj):
        return self.get_related_link(
            obj,
            "contacts",
            "groups__id__exact",
            f"{obj.contacts_count} contacts",
        )

    @admin.action(description="Send email to selected groups", permissions=["view"])
    def send_email(self, request, queryset):
        ids = ",".join(map(str, queryset.values_list("id", flat=True)))
        return redirect(reverse("admin:emails_email_add") + "?groups=" + ids)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.predefined:
            return False
        return super().has_delete_permission(request, obj=obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.predefined:
            return False
        return super().has_change_permission(request, obj=obj)
