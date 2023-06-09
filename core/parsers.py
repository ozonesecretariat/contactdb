import logging
from datetime import datetime

from django.db.models.functions import Trim, Lower
from django.utils.timezone import make_aware

from core.models import (
    KronosEvent,
    Organization,
    RegistrationStatus,
    Record,
    TemporaryContact,
)
from core.utils import check_diff


class KronosEventsParser:
    def __init__(self, task=None):
        self.task = task

    def parse_event_list(self, event_list):
        count_created = 0
        count_updated = 0
        for event_dict in event_list:
            try:
                if self.task:
                    self.task.log(
                        logging.INFO, f"Saving event: {event_dict.get('title')}"
                    )

                d = {
                    "event_id": event_dict.get("eventId"),
                    "title": event_dict.get("title"),
                    "code": event_dict.get("code"),
                    "start_date": make_aware(
                        datetime.strptime(
                            event_dict.get("startDate"), "%Y-%m-%dT%H:%M:%SZ"
                        )
                    ),
                    "end_date": make_aware(
                        datetime.strptime(
                            event_dict.get("endDate"), "%Y-%m-%dT%H:%M:%SZ"
                        )
                    ),
                    "venue_country": event_dict.get("venueCountry"),
                    "venue_city": event_dict.get("venueCity"),
                    "dates": event_dict.get("dates"),
                }
                created, attr_changes = self.save_event(d)

                if created:
                    count_created += 1
                    if self.task:
                        self.task.log(
                            logging.INFO, f"New event added: {event_dict.get('title')}"
                        )
                elif attr_changes:
                    count_updated += 1
                    if self.task:
                        self.task.log(
                            logging.INFO, f"Event updated: {event_dict.get('title')}"
                        )

            except Exception as e:
                if self.task:
                    self.task.log(
                        logging.WARN, f"Failed to save event: {event_dict.get('title')}"
                    )
        return count_created, count_updated

    @staticmethod
    def save_event(event_dict):
        old_event = KronosEvent.objects.filter(
            event_id=event_dict.get("event_id")
        ).first()
        new_event, created = KronosEvent.objects.update_or_create(
            event_id=event_dict["event_id"],
            defaults=event_dict,
        )

        attr_changes = {}
        for attr, value in event_dict.items():
            old_value = getattr(old_event, str(attr), None)
            if str(value) != str(old_value):
                attr_changes[attr] = (old_value, value)
        return created, attr_changes


class KronosParticipantsParser:
    def __init__(self, task=None):
        self.task = task

    def parse_contact_list(self, contact_list):
        for contact_dict in contact_list:
            try:
                organization_dict = contact_dict.get("organization")
                organization_defaults = {
                    "organization_id": organization_dict.get("organizationId"),
                    "name": organization_dict.get("name"),
                    "acronym": organization_dict.get("acronym"),
                    "organization_type_id": organization_dict.get("organizationTypeId"),
                    "organization_type": organization_dict.get("organizationType"),
                    "government": organization_dict.get("government", ""),
                    "government_name": organization_dict.get("governmentName", ""),
                    "country": organization_dict.get("country", ""),
                    "country_name": organization_dict.get("countryName", ""),
                }
                organization, _ = Organization.objects.get_or_create(
                    organization_id=organization_dict.get("organizationId"),
                    defaults=organization_defaults,
                )
                contact = (
                    Record.objects.annotate(
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
                    "country": contact_dict.get("country", ""),
                    "postal_code": contact_dict.get("postalCode", ""),
                    "birth_date": birth_date,
                }
                if contact:
                    if check_diff(contact, contact_defaults):
                        if self.task:
                            self.task.log(
                                logging.INFO,
                                f"A contact with the same name and emails as {contact_dict.get('contactId')} is already in database;"
                                f" adding it to the temporary table for conflict resolution",
                            )
                        contact_defaults["record"] = contact
                        TemporaryContact.objects.get_or_create(
                            contact_id=contact_dict.get("contactId"),
                            emails=contact_dict.get("emails"),
                            defaults=contact_defaults,
                        )
                    else:
                        if self.task:
                            self.task.log(
                                logging.INFO,
                                f"A contact with the same data as {contact_dict.get('contactId')} is already in database;",
                            )
                else:
                    contact, _ = Record.objects.get_or_create(
                        contact_id=contact_dict.get("contactId"),
                        emails=contact_dict.get("emails"),
                        defaults=contact_defaults,
                    )
                for registration in contact_dict["registrationStatuses"]:
                    if registration is not None:
                        RegistrationStatus.objects.get_or_create(
                            contact=contact,
                            event=KronosEvent.objects.filter(
                                event_id=registration.get("eventId")
                            ).first(),
                            code=registration.get("code"),
                            status=registration.get("status"),
                            date=registration.get("date"),
                            is_funded=registration.get("isFunded"),
                            role=registration.get("role", None),
                            priority_pass_code=registration.get("priorityPassCode", ""),
                            tags=registration.get("tags", []),
                        )

            except Exception as e:
                if self.task:
                    self.task.log(
                        logging.WARN,
                        f"The next error occurred while trying to save contact {contact_dict.get('contact_id')}: {e}",
                    )
