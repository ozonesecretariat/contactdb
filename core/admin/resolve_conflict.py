from copy import copy
from itertools import chain

from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages
from django.core.management import call_command
from django.utils.html import format_html

from common.urls import reverse
from core.admin import ContactAdminBase
from core.admin.contact_base import MERGE_FROM_PARAM
from core.models import Contact, ResolveConflict
from core.parsers import ContactParser


@admin.register(ResolveConflict)
class ResolveConflictAdmin(ContactAdminBase):
    show_index_page_count = True
    search_fields = (
        "first_name__unaccent",
        "last_name__unaccent",
        "designation__unaccent",
        "department__unaccent",
        "emails",
        "organization__name__unaccent",
        "organization__country__name__unaccent",
        "existing_contact__first_name__unaccent",
        "existing_contact__last_name__unaccent",
        "existing_contact__designation__unaccent",
        "existing_contact__department__unaccent",
        "existing_contact__emails",
        "existing_contact__organization__name__unaccent",
        "existing_contact__organization__country__name__unaccent",
    )
    list_filter = (
        AutocompleteFilterFactory("organization", "organization"),
        AutocompleteFilterFactory("country", "country"),
        "org_head",
        "is_use_organization_address",
    )
    list_display = (
        "existing_contact_link",
        "conflicting_contact",
    )
    list_display_links = (
        "existing_contact_link",
        "conflicting_contact",
    )
    prefetch_related = (
        "organization",
        "organization__country",
        "existing_contact",
        "existing_contact__organization",
        "existing_contact__organization__country",
    )
    actions = ("accept_new_data", "keep_both_contacts")

    @admin.action(
        description="Accept new data for selected conflicts", permissions=["delete"]
    )
    def accept_new_data(self, request, queryset):
        new_contacts = list(queryset)
        for temp_contact in new_contacts:
            self.save_incoming_data(temp_contact)

        self.message_user(
            request,
            f"{len(new_contacts)} conflicts resolved",
            messages.SUCCESS,
        )

    @admin.action(
        description="Keep both contacts",
        permissions=["delete"],
    )
    def keep_both_contacts(self, request, queryset):
        """
        If contact has multiple contact ids (is a merged contact), all
        contact_ids will be reimported. Useful when merging by accident.
        """

        contacts = (
            Contact.objects.filter(conflicting_contacts__in=queryset)
            .distinct()
            .values_list("contact_ids", flat=True)
        )

        kronos_ids = set(chain.from_iterable(contacts))

        contact_parser = ContactParser()
        for kronos_id in kronos_ids:
            contact_parser.import_contact_with_registrations(kronos_id)

    @staticmethod
    def save_incoming_data(incoming_contact):
        record = incoming_contact.existing_contact
        update_values = copy(dict(vars(incoming_contact)))
        update_values.pop("existing_contact_id")
        update_values.pop("id")
        for key, value in update_values.items():
            setattr(record, key, value)
        record.save()
        ResolveConflict.objects.filter(pk=incoming_contact.id).first().delete()

    def _link_to_conflict_resolution(self, obj, text):
        next_url = reverse("admin:core_resolveconflict_changelist")
        url = reverse(
            "admin:core_contact_change",
            kwargs={"object_id": obj.existing_contact.id},
            query={
                MERGE_FROM_PARAM: obj.pk,
                self.redirect_field_name: next_url,
            },
        )
        return format_html('<a href="{url}">{text}</a>', url=url, text=text)

    @admin.display(description="Existing contact")
    def existing_contact_link(self, obj):
        return self._link_to_conflict_resolution(obj, obj.existing_contact)

    @admin.display(description="Conflicting contact")
    def conflicting_contact(self, obj):
        return self.get_object_display_link(obj)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
