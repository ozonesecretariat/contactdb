import logging
from datetime import datetime

from django.db.models.functions import Trim, Lower
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
                "title": event_dict.get("title"),
                "code": event_dict.get("code"),
                "start_date": make_aware(
                    datetime.strptime(event_dict.get("startDate"), "%Y-%m-%dT%H:%M:%SZ")
                ),
                "end_date": make_aware(
                    datetime.strptime(event_dict.get("endDate"), "%Y-%m-%dT%H:%M:%SZ")
                ),
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
    def create_registrations(self, contact_dict, contact):
        for registration in contact_dict["registrationStatuses"]:
            if registration is None:
                continue

            event = Event.objects.filter(event_id=registration["eventId"]).first()
            status_kronos_id = registration["status"]
            status = RegistrationStatus.objects.get_or_create(
                kronos_id=status_kronos_id,
                defaults={
                    "name": status_kronos_id,
                },
            )[0]
            role_kronos_id = registration.get("role")
            role = RegistrationRole.objects.get_or_create(
                kronos_id=role_kronos_id,
                defaults={
                    "name": role_kronos_id,
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
            organization = self.get_org(contact_dict.get("organization", {}))

            contact = (
                Contact.objects.annotate(
                    trim_first_name=Lower(Trim("first_name")),
                    trim_last_name=Lower(Trim("last_name")),
                )
                .filter(
                    emails=contact_dict.get("emails"),
                    trim_first_name=contact_dict["firstName"].strip().lower(),
                    trim_last_name=contact_dict["lastName"].strip().lower(),
                )
                .first()
            )
            birth_date_string = contact_dict.get("dateOfBirth", "")
            if birth_date_string:
                birth_date = datetime.strptime(birth_date_string, "%Y-%m-%d").date()
            else:
                birth_date = None

            contact_defaults = {
                "contact_id": contact_dict.get("contactId"),
                "organization": organization,
                "title": contact_dict.get("title"),
                "first_name": contact_dict.get("firstName"),
                "last_name": contact_dict.get("lastName"),
                "designation": contact_dict.get("designation"),
                "department": contact_dict.get("department"),
                "affiliation": contact_dict.get("affiliation"),
                "phones": contact_dict.get("phones"),
                "mobiles": contact_dict.get("mobiles"),
                "faxes": contact_dict.get("faxes"),
                "emails": contact_dict.get("emails"),
                "email_ccs": contact_dict.get("emailCcs"),
                "notes": contact_dict.get("notes"),
                "is_in_mailing_list": contact_dict.get("isInMailingList"),
                "is_use_organization_address": contact_dict.get(
                    "isUseOrganizationAddress"
                ),
                "address": contact_dict.get("address", ""),
                "city": contact_dict.get("city", ""),
                "state": contact_dict.get("state", ""),
                "country": self.get_country(
                    contact_dict.get("country"),
                    contact_dict.get("countryName"),
                ),
                "postal_code": contact_dict.get("postalCode", ""),
                "birth_date": birth_date,
            }
            if contact:
                if check_diff(contact, contact_defaults):
                    self.task.log(
                        logging.INFO,
                        f"A contact with the same name and emails as {contact_dict.get('contactId')} is already in database;"
                        f" adding it to the temporary table for conflict resolution",
                    )
                    contact_defaults["existing_contact"] = contact
                    conflict, created = ResolveConflict.objects.get_or_create(
                        contact_id=contact_dict.get("contactId"),
                        emails=contact_dict.get("emails"),
                        defaults=contact_defaults,
                    )
                    self.task.conflicts_nr += created
                else:
                    self.task.log(
                        logging.INFO,
                        f"A contact with the same data as {contact_dict.get('contactId')} is already in database;",
                    )
                    self.task.skipped_nr += 1
            else:
                contact, created = Contact.objects.get_or_create(
                    contact_id=contact_dict.get("contactId"),
                    emails=contact_dict.get("emails"),
                    defaults=contact_defaults,
                )
                self.task.contacts_nr += created
                self.task.skipped_nr += not created
                if created:
                    self.task.log(logging.INFO, "Created contact: %s", contact)
            self.create_registrations(contact_dict, contact)
