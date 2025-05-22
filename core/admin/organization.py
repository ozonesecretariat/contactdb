from admin_auto_filters.filters import AutocompleteFilterFactory
from django import forms
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html_join
from import_export.admin import ExportMixin

from common.model_admin import ModelAdmin
from core.models import Organization


class OrganizationAdminForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            "name",
            "acronym",
            "organization_type",
            "country",
            "government",
            "primary_contacts",
            "secondary_contacts",
            "include_in_invitation",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # For now, limit choices to contacts belonging to this organization
            self.fields["primary_contacts"].queryset = self.instance.contacts.all()
            self.fields["secondary_contacts"].queryset = self.instance.contacts.all()

    def clean(self):
        cleaned_data = super().clean()
        primary = set(cleaned_data.get("primary_contacts", []))
        secondary = set(cleaned_data.get("secondary_contacts", []))

        # Checking for primary/secondary sets intersection
        if primary & secondary:
            raise forms.ValidationError(
                f"Contacts cannot be both primary and secondary: {primary & secondary}"
            )
        return cleaned_data


@admin.register(Organization)
class OrganizationAdmin(ExportMixin, ModelAdmin):
    form = OrganizationAdminForm
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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:  # Adding new organization
            form.base_fields["primary_contacts"].widget.can_add_related = False
            form.base_fields["secondary_contacts"].widget.can_add_related = False
        return form

    @admin.display(description="Contacts", ordering="contacts_count")
    def contacts_count(self, obj):
        return self.get_related_link(
            obj,
            "contacts",
            "organization",
            f"{obj.contacts_count} contacts",
        )

    @admin.display(description="Primary Contacts")
    def display_primary_contacts(self, obj):
        return (
            format_html_join(
                ", ", "{}", ((str(contact),) for contact in obj.primary_contacts.all())
            )
            or "-"
        )

    @admin.display(description="Secondary Contacts")
    def display_secondary_contacts(self, obj):
        return (
            format_html_join(
                ", ",
                "{}",
                ((str(contact),) for contact in obj.secondary_contacts.all()),
            )
            or "-"
        )
