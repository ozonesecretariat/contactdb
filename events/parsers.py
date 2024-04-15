import logging
import re
from datetime import datetime

from django.utils.timezone import make_aware

from core.models import (
    Country,
    Organization,
    Contact,
    OrganizationType,
    ResolveConflict,
)
from events.models import (
    Event,
    Registration,
    RegistrationRole,
    RegistrationStatus,
    RegistrationTag,
)
from common.utils import check_diff


class KronosParser:
    def __init__(self, task):
        self.task = task

    def parse_email_list(self, email_list):
        if isinstance(email_list, str):
            email_list = [email_list]

        result = set()
        for item in email_list:
            result.update(re.split(r"[;,]", item))

        return list(result)

    def parse_date(self, value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    def parse_datetime(self, value):
        return make_aware(datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ"))

    def get_country(self, code: str, name=None):
        if not code:
            return

        obj, created = Country.objects.get_or_create(
            code=code.upper(),
            defaults={"name": name},
        )
        obj.clean()
        obj.save()

        if created:
            self.task.log(logging.INFO, "Created Country: %r", obj)

        return obj

    def get_org_type(self, org_dict):
        obj, created = OrganizationType.objects.get_or_create(
            organization_type_id=org_dict["organizationTypeId"],
            defaults={"name": org_dict["organizationType"]},
        )
        if created:
            self.task.log(logging.INFO, "Created Organization Type: %r", obj)

        return obj

    def get_org(self, org_dict):
        if "organizationId" not in org_dict:
            return

        obj, created = Organization.objects.get_or_create(
            organization_id=org_dict["organizationId"],
            defaults={
                "name": org_dict.get("name"),
                "acronym": org_dict.get("acronym"),
                "organization_type": self.get_org_type(org_dict),
                "government": self.get_country(
                    org_dict.get("government"), org_dict.get("governmentName")
                ),
                "country": self.get_country(
                    org_dict.get("country"), org_dict.get("countryName")
                ),
            },
        )
        if created:
            self.task.log(logging.INFO, "Created Organization: %r", obj)

        return obj


class KronosEventsParser(KronosParser):
    def parse_event_list(self, event_list):
        count_created = 0
        count_updated = 0
        for event_dict in event_list:
            self.task.log(logging.INFO, f"Saving event: {event_dict.get('title')}")

            d = {
                "event_id": event_dict.get("eventId"),
                "title": event_dict.get("title", "").strip(),
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
                self.task.log(
                    logging.INFO, f"New event added: {event_dict.get('title')}"
                )
            elif attr_changes:
                count_updated += 1
                self.task.log(logging.INFO, f"Event updated: {event_dict.get('title')}")
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

    def parse_contact_list(self, contact_list):
        for contact_dict in contact_list:
            contact_id = contact_dict["contactId"]
            contact_dict["dateOfBirth"] = self.parse_date(
                contact_dict.get("dateOfBirth")
            )
            contact_dict["country"] = self.get_country(
                contact_dict.get("country"), contact_dict.get("countryName")
            )
            contact_dict["organization"] = self.get_org(
                contact_dict.get("organization", {})
            )
            contact_dict["emails"] = self.parse_email_list(contact_dict.get("emails"))
            contact_dict["emailCcs"] = self.parse_email_list(
                contact_dict.get("emailCcs")
            )

            contact_defaults = {
                model_attr: contact_dict.get(kronos_attr)
                for kronos_attr, model_attr in self.field_mapping.items()
            }

            contact = Contact.objects.filter(contact_id=contact_id).first()
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
                    contact_id=contact_id, **contact_defaults
                )
                self.task.contacts_nr += 1
                self.task.log(
                    logging.INFO, "Created contact %s: %s", contact, contact_id
                )
            self.create_registrations(contact_dict, contact)
