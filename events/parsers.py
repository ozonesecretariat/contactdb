import logging
import re
from datetime import UTC, datetime
from functools import cached_property

from django.db import IntegrityError, transaction
from django.db.models import Q

from common.parsing import parse_list
from core.models import (
    Contact,
    Country,
    Organization,
    OrganizationType,
    ResolveConflict,
)
from events.kronos import KronosClient
from events.models import (
    Event,
    PriorityPass,
    Registration,
    RegistrationRole,
    RegistrationTag,
)

KRONOS_STATUS_MAP = {
    1: Registration.Status.NOMINATED,
    2: Registration.Status.ACCREDITED,
    4: Registration.Status.REGISTERED,
}


def check_is_different(obj, dictionary):
    return any(getattr(obj, key) != value for key, value in dictionary.items())


class KronosParser:
    def __init__(self, task):
        self.task = task
        self.client = KronosClient()

    @cached_property
    def kronos_org_types(self):
        return {
            org_type["organizationTypeId"]: org_type
            for org_type in self.client.get_org_types()
        }

    def parse_date(self, value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").astimezone(UTC).date()
        except (TypeError, ValueError):
            return None

    def parse_datetime(self, value):
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").astimezone(UTC)

    def get_country(self, code: str):
        if not code:
            return None

        code = code.upper()
        try:
            return Country.objects.get(code=code)
        except Country.DoesNotExist:
            pass

        self.task.log(logging.INFO, "Creating Country: %s", code)
        return self._create_country(code)

    def _create_country(self, code):
        with transaction.atomic():
            try:
                obj = Country(code=code)
                obj.clean()
                obj.save()
                self.task.log(logging.INFO, "Created Country: %r", obj)
                return obj
            except IntegrityError:
                # Race condition - another worker created it while we were working
                self.task.log(
                    logging.INFO, "Country %s created by another worker", code
                )
                return Country.objects.get(code=code)

    def get_org_type(self, org_dict):
        org_type_id = org_dict["organizationTypeId"]
        try:
            return OrganizationType.objects.get(organization_type_id=org_type_id)
        except OrganizationType.DoesNotExist:
            pass

        org_type = self.kronos_org_types[org_type_id]
        obj = OrganizationType.objects.create(
            organization_type_id=org_type_id,
            acronym=org_type["acronym"].strip(),
            title=org_type["title"].strip(),
            description=org_type["description"].strip(),
        )
        self.task.log(logging.INFO, "Created Organization Type: %r", obj)
        return obj


class KronosEventsParser(KronosParser):
    def parse_event_list(self):
        count_created = 0
        count_updated = 0
        for event_dict in self.client.get_meetings():
            title = event_dict.get("title", "").strip()
            self.task.log(logging.INFO, "Saving event: %s", title)

            d = {
                "event_id": event_dict.get("eventId"),
                "title": title,
                "code": event_dict.get("code"),
                "start_date": self.parse_datetime(event_dict["startDate"]),
                "end_date": self.parse_datetime(event_dict["endDate"]),
                "venue_country": self.get_country(event_dict.get("venueCountry")),
                "venue_city": event_dict.get("venueCity"),
                "dates": event_dict.get("dates"),
            }
            created, attr_changes = self.save_event(d)

            if created:
                count_created += 1
                self.task.log(logging.INFO, "New event added: %s", title)
            elif attr_changes:
                count_updated += 1
                self.task.log(logging.INFO, "Event updated: %s", title)
        return count_created, count_updated

    @staticmethod
    def save_event(event_dict):
        old_event = Event.objects.filter(event_id=event_dict.get("event_id")).first()
        new_event, created = Event.objects.update_or_create(
            event_id=event_dict["event_id"],
            defaults=event_dict,
        )

        attr_changes = {}
        for attr, value in event_dict.items():
            old_value = getattr(old_event, str(attr), None)
            if str(value) != str(old_value):
                attr_changes[attr] = (old_value, value)
        return created, attr_changes


class KronosParticipantsParser(KronosParser):
    field_mapping = {
        "organization": "organization",
        "title": "title",
        "firstName": "first_name",
        "lastName": "last_name",
        "designation": "designation",
        "department": "department",
        "affiliation": "affiliation",
        "phones": "phones",
        "mobiles": "mobiles",
        "faxes": "faxes",
        "emails": "emails",
        "emailCcs": "email_ccs",
        "notes": "notes",
        "isUseOrganizationAddress": "is_use_organization_address",
        "address": "address",
        "city": "city",
        "state": "state",
        "country": "country",
        "postalCode": "postal_code",
        "dateOfBirth": "birth_date",
    }

    def __init__(self, task):
        super().__init__(task=task)
        self.event: Event = task.event

    def get_org(self, org_dict):
        if "organizationId" not in org_dict:
            return None

        org_type = self.get_org_type(org_dict)
        if org_type.acronym.lower() == "gov":
            # GOV orgs have the invite "flag" manually included in notes in Kronos.
            # So it's "safe" to import it as is, because they have been validated,
            # manually there.
            include_in_invitation = "#invite" in org_dict.get("notes", "")
        else:
            # For other types of orgs, the notes don't include the invite status.
            # So as a default, include orgs that have participated in recent events.
            # Users will need to validate if this is correct or not.
            include_in_invitation = (
                self.event.start_date and self.event.start_date.year >= 2024
            )

        obj, created = Organization.objects.get_or_create(
            organization_id=org_dict["organizationId"],
            defaults={
                "name": org_dict.get("name", "").strip(),
                "acronym": org_dict.get("acronym", "").strip(),
                "organization_type": org_type,
                "government": self.get_country(org_dict.get("government")),
                "country": self.get_country(org_dict.get("country")),
                "state": org_dict.get("state", "").strip(),
                "city": org_dict.get("city", "").strip(),
                "postal_code": org_dict.get("postalCode", "").strip(),
                "address": org_dict.get("address", "").strip(),
                "phones": org_dict.get("phones", []),
                "faxes": org_dict.get("faxes", []),
                "websites": org_dict.get("webs", []),
                "emails": parse_list(org_dict.get("emails", [])),
                "email_ccs": parse_list(org_dict.get("emailCcs", [])),
                "include_in_invitation": include_in_invitation,
            },
        )
        if created:
            self.task.log(logging.INFO, "Created Organization: %r", obj)
        elif include_in_invitation and not obj.include_in_invitation:
            # Org was initially created from an older event, so we need to update it
            # here. Override even if users have made manual changes since then, as that
            # is very unlikely.
            obj.include_in_invitation = True
            obj.save()

        return obj

    def get_priority_pass(self, code):
        if not code:
            return PriorityPass.objects.create()
        return PriorityPass.objects.get_or_create(code=code)[0]

    def create_registrations(self, contact_dict, contact):
        for registration in contact_dict["registrationStatuses"]:
            if registration is None:
                continue

            event = Event.objects.filter(event_id=registration["eventId"]).first()
            role_kronos_enum = registration.get("role")
            role = RegistrationRole.objects.get_or_create(
                kronos_value=role_kronos_enum,
                defaults={
                    "name": role_kronos_enum,
                },
            )[0]

            obj, created = Registration.objects.get_or_create(
                contact=contact,
                event=event,
                defaults={
                    "status": KRONOS_STATUS_MAP[registration["status"]],
                    "role": role,
                    "date": registration.get("date"),
                    "is_funded": registration.get("isFunded"),
                    "priority_pass": self.get_priority_pass(
                        registration.get("priorityPassCode", "")
                    ),
                    "organization": contact.organization,
                    "designation": contact.designation,
                    "department": contact.department,
                },
            )
            self.task.registrations_nr += created

            for tag in registration.get("tags", []):
                tag = tag.strip()
                if tag:
                    tag = RegistrationTag.objects.get_or_create(name=tag)[0]
                    obj.tags.add(tag)
            self.task.log(
                logging.INFO,
                "Added meeting registration for %r event: %s",
                contact,
                event,
            )

    def parse_contact_list(self):
        event_orgs = {
            org["organizationId"]: org
            for org in self.client.get_organizations_for_event(self.event.event_id)
        }

        for contact_dict in self.client.get_participants(self.event.event_id):
            # The organization dict in the contact dict is not complete, replace it
            # the full version from the other API if available.
            org_id = contact_dict.get("organization", {}).get("organizationId", None)
            try:
                contact_dict["organization"] = event_orgs[org_id]
            except KeyError:
                self.task.log(
                    logging.WARNING,
                    "Could not find full organization info for org: %s",
                    org_id,
                )

            self._handle_contact(contact_dict)

        # Handle M2M relationship for Org
        for org_dict in event_orgs.values():
            try:
                org = Organization.objects.get(
                    organization_id=org_dict["organizationId"]
                )
            except Organization.DoesNotExist:
                continue

            # Ignore if any contacts are not found, as they should be found whenever
            # we parse the event they participated in. Otherwise, the email/email_ccs
            # are still available in the org's fields.
            org.primary_contacts.add(*org.filter_contacts_by_emails(org.emails))
            org.secondary_contacts.add(*org.filter_contacts_by_emails(org.email_ccs))

    def _handle_contact(self, contact_dict):
        contact_id = contact_dict["contactId"]
        contact_dict["dateOfBirth"] = self.parse_date(contact_dict.get("dateOfBirth"))
        contact_dict["country"] = self.get_country(contact_dict.get("country"))
        contact_dict["organization"] = self.get_org(
            contact_dict.get("organization", {})
        )
        contact_dict["emails"] = parse_list(contact_dict.get("emails"))
        contact_dict["emailCcs"] = parse_list(contact_dict.get("emailCcs"))

        langs = self.get_languages(contact_dict.get("notes", ""))

        contact_defaults = {
            model_attr: contact_dict.get(kronos_attr)
            for kronos_attr, model_attr in self.field_mapping.items()
        } | langs

        contact = (
            Contact.objects.filter(contact_ids__contains=[contact_id])
            .prefetch_related("conflicting_contacts")
            .first()
        )
        if contact:
            self._handle_conflict(contact, contact_id, contact_defaults)
        else:
            contact = self._create_contact(contact_id, contact_defaults)
        self.create_registrations(contact_dict, contact)

    def _handle_conflict(self, contact, contact_id, contact_defaults):
        if not check_is_different(contact, contact_defaults):
            # The imported contact is identical to the one in the database currently
            self._skip_contact(contact, contact_id)
            return None

        for existing_conflict in contact.conflicting_contacts.all():
            if not check_is_different(existing_conflict, contact_defaults):
                # We found an identical conflict already in the database
                self._skip_contact(contact, contact_id)
                return None

        return self._create_conflict(contact, contact_id, contact_defaults)

    def _create_conflict(self, contact, contact_id, contact_defaults):
        self.task.log(
            logging.INFO,
            "A contact with the ID as %s is already in database; "
            "adding it to the temporary table for conflict resolution: %s",
            contact_id,
            contact,
        )
        self.task.conflicts_nr += 1
        return ResolveConflict.objects.create(
            existing_contact=contact, **contact_defaults
        )

    def _skip_contact(self, contact, contact_id):
        self.task.log(
            logging.INFO,
            "A contact with the same data as %s is already in database: %s",
            contact,
            contact_id,
        )
        self.task.skipped_nr += 1

    def _create_contact(self, contact_id, contact_defaults):
        contact = Contact.objects.create(contact_ids=[contact_id], **contact_defaults)
        self.task.contacts_nr += 1
        self.task.log(logging.INFO, "Created contact %s: %s", contact, contact_id)
        return contact

    @classmethod
    def get_languages(cls, note_field: str | None) -> dict:
        """
        Extracts language codes from the notes field of a contact.

        Eg: Contact with note "Picture #92520\r\n##E\r\n##R" represents:
            - Primary language: English (##E)
            - Secondary language: Russian (##R)

        Other codes:
        ##F (French), ##A (Arabic), ##S (Spanish),##C (Chinese)
        """

        langs = re.findall(r"##([EFSACR])", note_field) if note_field else []
        if not langs:
            return {}

        return {
            "primary_lang": langs[0] if len(langs) > 0 else "",
            "second_lang": langs[1] if len(langs) > 1 else "",
            "third_lang": langs[2] if len(langs) > 2 else "",
        }


class KronosOrganizationsParser(KronosParser):
    """
    Parser to be used in separate import of Organizations.
    """

    def __init__(self, task):
        super().__init__(task=task)

    def parse_organizations_list(self):
        existing_ids = Organization.objects.values_list("organization_id", flat=True)
        for org_dict in self.client.get_all_organizations():
            if org_dict.get("organizationId") in existing_ids:
                continue

            org_type = self.get_org_type(org_dict)
            # TODO: is this actually OK?
            include_in_invitation = "#invite" in org_dict.get("notes", "")

            organization, created = Organization.objects.get_or_create(
                organization_id=org_dict["organizationId"],
                defaults={
                    "name": org_dict.get("name", "").strip(),
                    "acronym": org_dict.get("acronym", "").strip(),
                    "organization_type": org_type,
                    "government": self.get_country(org_dict.get("government")),
                    "country": self.get_country(org_dict.get("country")),
                    "state": org_dict.get("state", "").strip(),
                    "city": org_dict.get("city", "").strip(),
                    "postal_code": org_dict.get("postalCode", "").strip(),
                    "address": org_dict.get("address", "").strip(),
                    "phones": org_dict.get("phones", []),
                    "faxes": org_dict.get("faxes", []),
                    "websites": org_dict.get("webs", []),
                    "emails": parse_list(org_dict.get("emails", [])),
                    "email_ccs": parse_list(org_dict.get("emailCcs", [])),
                    "include_in_invitation": include_in_invitation,
                },
            )
            if created:
                self.task.log(logging.INFO, "Created Organization: %r", organization)
                self.task.organizations_nr += 1

                # Find and associate primary & secondary contacts by email
                matching_primaries = Contact.objects.filter(
                    Q(emails__overlap=organization.emails)
                    | Q(email_ccs__overlap=organization.emails)
                )
                matching_secondaries = Contact.objects.filter(
                    Q(emails__overlap=organization.email_ccs)
                    | Q(email_ccs__overlap=organization.email_ccs)
                )
                matching_contacts = [
                    (True, contact) for contact in matching_primaries
                ] + [
                    (False, contact)
                    for contact in matching_secondaries
                    # Avoiding duplicates between secondaries & primaries
                    if contact not in matching_primaries
                ]
                for is_primary, contact in matching_contacts:
                    if contact.organization and contact.organization != organization:
                        self.task.log(
                            logging.WARNING,
                            "Contact %r already belongs to %r, skipping association with %r",
                            contact,
                            contact.organization,
                            organization,
                        )
                        self.task.skipped_contacts_nr += 1
                        continue

                    if not contact.organization:
                        contact.organization = organization
                        contact.save()
                        self.task.log(
                            logging.INFO,
                            "Associated contact %r with organization %r %s",
                            contact,
                            organization,
                            "as primary" if is_primary else "as secondary",
                        )
                    if is_primary:
                        organization.primary_contacts.add(contact)
                    else:
                        organization.secondary_contacts.add(contact)
                    self.task.contacts_nr += 1
