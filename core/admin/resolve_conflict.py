from copy import copy
from itertools import chain

from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Q
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
        "country",
        "organization",
        "organization__country",
        "organization__government",
        "existing_contact",
        "existing_contact__organization",
        "existing_contact__organization__country",
        "existing_contact__organization__government",
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
        Convert conflicts to contacts. If a contact has multiple
        contact_ids (e.g. it's a merged Kronos contact), all contact_ids
        will be reimported from Kronos.
        """

        def create_contacts_from_conflicts(conflict_queryset) -> int:
            conflicts_dict = list(conflict_queryset.values())
            conflicts_ids = []

            with transaction.atomic():
                for conflict in conflicts_dict:
                    conflict.pop("existing_contact_id", None)
                    conflict_id = conflict.pop("id", None)
                    conflicts_ids.append(conflict_id)

                    Contact.objects.create(**conflict)

                ResolveConflict.objects.filter(pk__in=conflicts_ids).delete()
            return len(conflicts_ids)

        # Handle conflicts with no contact_ids
        no_contact_ids_qs = queryset.filter(
            Q(existing_contact__contact_ids__isnull=True)
            | Q(existing_contact__contact_ids=[])
        ).values()
        count_created = create_contacts_from_conflicts(no_contact_ids_qs)

        if count_created:
            self.message_user(
                request,
                f"Created {count_created} contacts from conflicts.",
                messages.SUCCESS,
            )

        # Reimport contacts with contact_ids from Kronos
        kronos_contacts = (
            Contact.objects.filter(
                conflicting_contacts__in=queryset, contact_ids__isnull=False
            )
            .exclude(contact_ids=[])
            .distinct()
        )

        if kronos_contacts.exists():
            kronos_ids = set(
                chain.from_iterable(
                    kronos_contacts.values_list("contact_ids", flat=True)
                )
            )

            # Convert all related conflicts to contacts before
            # reimporting
            related_conflicts = ResolveConflict.objects.filter(
                existing_contact__in=kronos_contacts
            )
            count_created = create_contacts_from_conflicts(related_conflicts)

            if count_created:
                self.message_user(
                    request,
                    f"Created {count_created} contacts from conflicts.",
                    messages.SUCCESS,
                )

            contact_parser = ContactParser()
            imported_contacts = contact_parser.import_contacts_with_registrations(
                kronos_ids
            )

            if imported_contacts:
                self.message_user(
                    request,
                    f"Reimported {len(imported_contacts)} contacts with registrations from Kronos.",
                    messages.SUCCESS,
                )

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
