from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django_object_actions import DjangoObjectActions, action

from common.array_field import ArrayFilterFactory, ArrayLength
from common.audit import bulk_audit_create
from common.model_admin import ModelAdmin
from common.permissions import has_model_permission
from common.urls import reverse
from core.admin import MergeContacts
from core.models import (
    Contact,
    DismissedDuplicateContact,
    DismissedDuplicateOrganization,
    Organization,
    PossibleDuplicateContact,
    PossibleDuplicateOrganization,
)


class IsDismissedFilter(admin.SimpleListFilter):
    title = "dismissed"
    parameter_name = "is_dismissed"

    def lookups(self, request, model_admin):
        return [
            ("0", "No"),
            ("1", "Yes"),
        ]

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == str(lookup),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": title,
            }

    def queryset(self, request, queryset):
        val = self.value()
        if val == "0" or val is None:
            return queryset.filter(is_dismissed=False)
        if val == "1":
            return queryset.filter(is_dismissed=True)
        return queryset.none()


@admin.register(PossibleDuplicateContact)
class PossibleDuplicateContactAdmin(MergeContacts, DjangoObjectActions, ModelAdmin):
    show_index_page_count = True
    list_display = (
        "identical_values",
        "contacts_display",
        "organization_display",
        "inline_actions",
    )
    list_filter = (
        IsDismissedFilter,
        ArrayFilterFactory("duplicate_fields", "duplicate field"),
        "contacts__groups",
        AutocompleteFilterFactory("organization", "contacts__organization"),
        AutocompleteFilterFactory("country", "contacts__country"),
    )
    search_fields = (
        "duplicate_values",
        "contacts__first_name",
        "contacts__last_name",
        "contacts__designation",
        "contacts__department",
        "contacts__emails",
        "contacts__email_ccs",
    )
    prefetch_related = (
        "contacts",
        "contacts__organization",
        "contacts__organization__country",
        "contacts__organization__government",
    )
    annotate_query = {
        "field_count": ArrayLength("duplicate_fields"),
        "contact_count": ArrayLength("contact_ids"),
    }
    fields = (
        "identical_values",
        ("contacts_display", "organization_display"),
        "is_dismissed",
    )
    change_actions = ("merge_possible_duplicate", "dismiss_duplicate")
    actions = ("dismiss_duplicates",)

    def get_index_page_count(self):
        return self.model.objects.filter(is_dismissed=False).count()

    def get_queryset(self, *args, **kwargs):
        return (
            super()
            .get_queryset(*args, **kwargs)
            .order_by("-field_count", "-contact_count")
        )

    @admin.display(description="Actions")
    def inline_actions(self, obj):
        return mark_safe(
            " ".join(
                [
                    self.get_inline_action(obj, "merge_possible_duplicate", "default"),
                    self.get_inline_action(obj, "dismiss_duplicate"),
                ]
            )
        )

    def has_resolve_duplicates_permission(self, request):
        return (
            self.has_view_permission(request)
            and has_model_permission(request, Contact, "change")
            and has_model_permission(request, Contact, "delete")
        )

    @action(
        label="Merge",
        description="Merge contacts",
        permissions=["resolve_duplicates"],
    )
    def merge_possible_duplicate(self, request, obj):
        return self.merge_action(request, obj.contacts.all())

    @action(
        label="Dismiss",
        description="Dismiss this potential duplicate",
        permissions=["resolve_duplicates"],
    )
    def dismiss_duplicate(self, request, obj):
        DismissedDuplicateContact.objects.get_or_create(contact_ids=obj.contact_ids)
        self.message_user(
            request,
            "Possible duplicate dismissed",
            level=messages.SUCCESS,
        )
        return redirect(self.get_admin_list_link(self.model))

    @action(
        label="Dismiss",
        description="Dismiss selected duplicates",
        permissions=["resolve_duplicates"],
    )
    def dismiss_duplicates(self, request, queryset):
        objs = DismissedDuplicateContact.objects.bulk_create(
            [
                DismissedDuplicateContact(contact_ids=duplicate.contact_ids)
                for duplicate in queryset
                if duplicate.contact_ids
            ],
        )
        bulk_audit_create(objs, request=request)

        self.message_user(
            request,
            f"{len(objs)} possible duplicates dismissed",
            level=messages.SUCCESS,
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    @admin.display(description="Identical values", ordering="id")
    def identical_values(self, obj):
        return mark_safe("<br/>".join(obj.duplicate_values))

    @admin.display(description="Contacts", ordering="contact_count")
    def contacts_display(self, obj):
        urls = []
        for contact in obj.contacts.all():
            url = reverse("admin:core_contact_change", args=(contact.id,))
            urls.append(f"<a href={url}>{contact.display_name}</a>")
        return mark_safe("<br/>".join(urls))

    @admin.display(description="Organization")
    def organization_display(self, obj):
        urls = []
        for contact in obj.contacts.all():
            if contact.organization:
                url = reverse(
                    "admin:core_organization_change", args=(contact.organization.id,)
                )
                urls.append(f"<a href={url}>{contact.organization}</a>")
            else:
                urls.append("-")
        return mark_safe("<br/>".join(urls))


@admin.register(PossibleDuplicateOrganization)
class PossibleDuplicateOrganizationAdmin(DjangoObjectActions, ModelAdmin):
    show_index_page_count = True
    list_display = (
        "identical_values",
        "organization_display",
        "inline_actions",
    )
    list_filter = (
        IsDismissedFilter,
        AutocompleteFilterFactory(
            "organization type", "organizations__organization_type"
        ),
        AutocompleteFilterFactory("government", "organizations__government"),
        AutocompleteFilterFactory("country", "organizations__country"),
    )
    search_fields = (
        "duplicate_values",
        "organizations__name",
        "organizations__alt_names",
        "organizations__acronym",
        "organizations__country__name",
        "organizations__government__name",
    )
    prefetch_related = (
        "organizations",
        "organizations__country",
        "organizations__government",
    )
    annotate_query = {
        "field_count": ArrayLength("duplicate_fields"),
        "organization_count": ArrayLength("organization_ids"),
    }
    fields = ("identical_values", "organization_display", "is_dismissed")
    change_actions = ("dismiss_duplicate",)
    actions = ("dismiss_duplicates",)

    def get_index_page_count(self):
        return self.model.objects.filter(is_dismissed=False).count()

    def get_queryset(self, *args, **kwargs):
        return (
            super()
            .get_queryset(*args, **kwargs)
            .order_by("-field_count", "-organization_count")
            .distinct()
        )

    @admin.display(description="Actions")
    def inline_actions(self, obj):
        return mark_safe(
            " ".join(
                [
                    # self.get_inline_action(obj, "merge_possible_duplicate", "default"),
                    self.get_inline_action(obj, "dismiss_duplicate"),
                ]
            )
        )

    def has_resolve_duplicates_permission(self, request):
        return (
            self.has_view_permission(request)
            and has_model_permission(request, Organization, "change")
            and has_model_permission(request, Organization, "delete")
        )

    #
    # @action(
    #     label="Merge",
    #     description="Merge contacts",
    #     permissions=["resolve_duplicates"],
    # )
    # def merge_possible_duplicate(self, request, obj):
    #     return self.merge_action(request, obj.contacts.all())

    @action(
        label="Dismiss",
        description="Dismiss this potential duplicate",
        permissions=["resolve_duplicates"],
    )
    def dismiss_duplicate(self, request, obj):
        DismissedDuplicateOrganization.objects.get_or_create(
            organization_ids=obj.organization_ids
        )
        self.message_user(
            request,
            "Possible duplicate dismissed",
            level=messages.SUCCESS,
        )
        return redirect(self.get_admin_list_link(self.model))

    @action(
        label="Dismiss",
        description="Dismiss selected duplicates",
        permissions=["resolve_duplicates"],
    )
    def dismiss_duplicates(self, request, queryset):
        objs = DismissedDuplicateOrganization.objects.bulk_create(
            [
                DismissedDuplicateOrganization(
                    organization_ids=duplicate.organization_ids
                )
                for duplicate in queryset
                if duplicate.organization_ids
            ],
        )
        bulk_audit_create(objs, request=request)

        self.message_user(
            request,
            f"{len(objs)} possible duplicates dismissed",
            level=messages.SUCCESS,
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    @admin.display(description="Identical values", ordering="id")
    def identical_values(self, obj):
        return mark_safe("<br/>".join(obj.duplicate_values))

    @admin.display(description="Organizations", ordering="organization_count")
    def organization_display(self, obj):
        urls = []
        for org in obj.organizations.all():
            url = reverse("admin:core_organization_change", args=(org.id,))
            urls.append(f"<a href={url}>{org}</a>")
        return mark_safe("<br/>".join(urls))
