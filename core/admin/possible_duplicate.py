from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django_object_actions import action, DjangoObjectActions
from common.array_field import ArrayFilterFactory, ArrayLength
from common.model_admin import ModelAdmin
from common.permissions import has_model_permission
from common.urls import reverse
from core.admin import MergeContacts
from core.models import Contact, DismissedDuplicate, PossibleDuplicate


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


@admin.register(PossibleDuplicate)
class PossibleDuplicateAdmin(MergeContacts, DjangoObjectActions, ModelAdmin):
    show_index_page_count = True
    list_display = (
        "identical_values",
        "contacts_display",
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
    )
    annotate_query = {
        "field_count": ArrayLength("duplicate_fields"),
        "contact_count": ArrayLength("contact_ids"),
    }
    fields = ("identical_values", "contacts_display", "is_dismissed")
    change_actions = ("merge_possible_duplicate", "dismiss_duplicate")
    inline_actions = change_actions
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
        DismissedDuplicate.objects.get_or_create(contact_ids=obj.contact_ids)
        self.message_user(
            request,
            f"Possible duplicate dismissed",
            level=messages.SUCCESS,
        )
        return redirect(self.get_admin_list_link(self.model))

    @action(
        label="Dismiss",
        description="Dismiss selected duplicates",
        permissions=["resolve_duplicates"],
    )
    def dismiss_duplicates(self, request, queryset):
        objs = DismissedDuplicate.objects.bulk_create(
            [
                DismissedDuplicate(contact_ids=duplicate.contact_ids)
                for duplicate in queryset
            ],
            ignore_conflicts=True,
        )
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
            urls.append(f"<a href={url}>{contact}</a>")
        return mark_safe("<br/>".join(urls))
