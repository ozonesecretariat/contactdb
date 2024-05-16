import logging
from datetime import datetime
from functools import cached_property

from django.utils.timezone import make_aware
from common.parsing import parse_list

from core.models import (
    Country,
    Organization,
    Contact,
    OrganizationType,
    ResolveConflict,
)
from events.kronos import KronosClient
from events.models import (
    Event,
    Registration,
    RegistrationRole,
    RegistrationStatus,
    RegistrationTag,
)


def check_diff(obj, dictionary):
    for key, value in dictionary.items():
        if getattr(obj, key) != value:
            return True
    return False


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
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    def parse_datetime(self, value):
        return make_aware(datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ"))

    def get_country(self, code: str):
        if not code:
            return

        obj, created = Country.objects.get_or_create(code=code.upper())
        obj.clean()
        obj.save()

        if created:
            self.task.log(logging.INFO, "Created Country: %r", obj)

        return obj

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

    def get_org(self, org_dict):
        if "organizationId" not in org_dict:
            return

        obj, created = Organization.objects.get_or_create(
            organization_id=org_dict["organizationId"],
            defaults={
                "name": org_dict.get("name", "").strip(),
                "acronym": org_dict.get("acronym", "").strip(),
                "organization_type": self.get_org_type(org_dict),
                "government": self.get_country(org_dict.get("government")),
                "country": self.get_country(org_dict.get("country")),
            },
        )
        if created:
            self.task.log(logging.INFO, "Created Organization: %r", obj)

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
        "isInMailingList": "is_in_mailing_list",
        "isUseOrganizationAddress": "is_use_organization_address",
        "address": "address",
        "city": "city",
        "state": "state",
        "country": "country",
        "postalCode": "postal_code",
        "dateOfBirth": "birth_date",
    }

    def create_registrations(self, contact_dict, contact):
        for registration in contact_dict["registrationStatuses"]:
            if registration is None:
                continue

            event = Event.objects.filter(event_id=registration["eventId"]).first()
            status_kronos_enum = registration["status"]
            status = RegistrationStatus.objects.get_or_create(
                kronos_value=status_kronos_enum,
                defaults={
                    "name": status_kronos_enum,
                },
            )[0]
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
                    "status": status,
                    "role": role,
                    "date": registration.get("date"),
                    "is_funded": registration.get("isFunded"),
                    "priority_pass_code": registration.get("priorityPassCode", ""),
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

    def parse_contact_list(self, event_id):
        for contact_dict in self.client.get_participants(event_id):
            contact_id = contact_dict["contactId"]
            contact_dict["dateOfBirth"] = self.parse_date(
                contact_dict.get("dateOfBirth")
            )
            contact_dict["country"] = self.get_country(contact_dict.get("country"))
            contact_dict["organization"] = self.get_org(
                contact_dict.get("organization", {})
            )
            contact_dict["emails"] = parse_list(contact_dict.get("emails"))
            contact_dict["emailCcs"] = parse_list(contact_dict.get("emailCcs"))

            contact_defaults = {
                model_attr: contact_dict.get(kronos_attr)
                for kronos_attr, model_attr in self.field_mapping.items()
            }

            contact = Contact.objects.filter(contact_ids__contains=[contact_id]).first()
            if contact:
                if check_diff(contact, contact_defaults):
                    self.task.log(
                        logging.INFO,
                        "A contact with the ID as %s is already in database; "
                        "adding it to the temporary table for conflict resolution: %s",
                        contact,
                        contact_id,
                    )
                    ResolveConflict.objects.create(
                        existing_contact=contact, **contact_defaults
                    )
                    self.task.conflicts_nr += 1
                else:
                    self.task.log(
                        logging.INFO,
                        "A contact with the same data as %s is already in database: %s",
                        contact,
                        contact_id,
                    )
                    self.task.skipped_nr += 1
            else:
                contact = Contact.objects.create(
                    contact_ids=[contact_id], **contact_defaults
                )
                self.task.contacts_nr += 1
                self.task.log(
                    logging.INFO, "Created contact %s: %s", contact, contact_id
                )
            self.create_registrations(contact_dict, contact)
