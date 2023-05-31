import logging
from datetime import datetime

from django.utils.timezone import make_aware

from core.models import KronosEvent, Organization, RegistrationStatus, Record
from core.temp_models import TemporaryContact
from core.utils import check_field


class KronosEventsParser:
    def __init__(self, task=None):
        self.task = task

    def parse_event_list(self, event_list):
        count_created = 0
        count_updated = 0
        for event_dict in event_list:
            try:
                try:
                    self.task.log(
                        logging.INFO, f"Saving event: {event_dict.get('title')}"
                    )
                except:
                    pass

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
                    try:
                        self.task.log(
                            logging.INFO, f"New event added: {event_dict.get('title')}"
                        )
                    except:
                        pass
                elif attr_changes:
                    count_updated += 1
                    try:
                        print(attr_changes)
                        self.task.log(
                            logging.INFO, f"Event updated: {event_dict.get('title')}"
                        )
                    except:
                        pass

            except Exception as e:
                print(e)
                try:
                    self.task.log(
                        logging.WARN, f"Failed to save event: {event_dict.get('title')}"
                    )
                except:
                    pass
        return count_created, count_updated

    @staticmethod
    def save_event(event_dict):
        old_event = KronosEvent.objects.filter(
            event_id=event_dict.get("event_id")
        ).first()
        new_event, created = KronosEvent.objects.update_or_create(
            event_id=event_dict["event_id"],
            defaults=dict(event_dict),
        )

        attr_changes = {}
        for attr, value in [(k, v) for (k, v) in event_dict.items()]:
            old_value = getattr(old_event, str(attr), None)
            if str(value) != str(old_value):
                attr_changes.update({attr: (old_value, value)})
        return created, attr_changes


class KronosParticipantsParser:
    def __init__(self, task=None):
        self.task = task

    def parse_contact_list(self, contact_list):
        for contact_dict in contact_list:
            try:
                organization_dict = contact_dict.get("organization")
                organization, _ = Organization.objects.get_or_create(
                    organization_id=organization_dict.get("organizationId"),
                    name=organization_dict.get("name"),
                    acronym=organization_dict.get("acronym"),
                    organization_type_id=organization_dict.get("organizationTypeId"),
                    organization_type=organization_dict.get("organizationType"),
                    government=check_field(organization_dict, "government"),
                    government_name=check_field(organization_dict, "governmentName"),
                    country=check_field(organization_dict, "country"),
                    country_name=check_field(organization_dict, "countryName"),
                )
                contact = Record.objects.filter(
                    contact_id=contact_dict.get("contactId")
                ).first()
                if contact:
                    TemporaryContact.objects.get_or_create(
                        contact_id=contact_dict.get("contactId"),
                        organization=organization,
                        title=contact_dict.get("title"),
                        first_name=contact_dict.get("firstName"),
                        last_name=contact_dict.get("lastName"),
                        designation=contact_dict.get("designation"),
                        department=contact_dict.get("department"),
                        affiliation=contact_dict.get("affiliation"),
                        phones=contact_dict.get("phones"),
                        mobiles=contact_dict.get("mobiles"),
                        faxes=contact_dict.get("faxes"),
                        emails=contact_dict.get("emails"),
                        email_ccs=contact_dict.get("emailCcs"),
                        notes=contact_dict.get("notes"),
                        is_in_mailing_list=contact_dict.get("isInMailingList"),
                        is_use_organization_address=contact_dict.get(
                            "isUseOrganizationAddress"
                        ),
                        address=check_field(contact_dict, "address"),
                        city=check_field(contact_dict, "city"),
                        state=check_field(contact_dict, "state"),
                        country=check_field(contact_dict, "country"),
                        postal_code=check_field(contact_dict, "postalCode"),
                        birth_date=check_field(contact_dict, "dateOfBirth"),
                    )
                else:
                    contact, _ = Record.objects.get_or_create(
                        contact_id=contact_dict.get("contactId"),
                        organization=organization,
                        title=contact_dict.get("title"),
                        first_name=contact_dict.get("firstName"),
                        last_name=contact_dict.get("lastName"),
                        designation=contact_dict.get("designation"),
                        department=contact_dict.get("department"),
                        affiliation=contact_dict.get("affiliation"),
                        phones=contact_dict.get("phones"),
                        mobiles=contact_dict.get("mobiles"),
                        faxes=contact_dict.get("faxes"),
                        emails=contact_dict.get("emails"),
                        email_ccs=contact_dict.get("emailCcs"),
                        notes=contact_dict.get("notes"),
                        is_in_mailing_list=contact_dict.get("isInMailingList"),
                        is_use_organization_address=contact_dict.get(
                            "isUseOrganizationAddress"
                        ),
                        address=check_field(contact_dict, "address"),
                        city=check_field(contact_dict, "city"),
                        state=check_field(contact_dict, "state"),
                        country=check_field(contact_dict, "country"),
                        postal_code=check_field(contact_dict, "postalCode"),
                        birth_date=check_field(contact_dict, "dateOfBirth"),
                    )
                for registration in contact_dict["registrationStatuses"]:
                    if registration is not None:
                        RegistrationStatus.objects.get_or_create(
                            contact=contact,
                            event_id=registration.get("eventId"),
                            code=registration.get("code"),
                            status=registration.get("status"),
                            date=registration.get("date"),
                            is_funded=registration.get("isFunded"),
                            role=check_field(registration, "role"),
                            priority_pass_code=check_field(
                                registration, "priorityPassCode"
                            ),
                            tags=check_field(registration, "tags"),
                        )

            except Exception as e:
                print(e)
                try:
                    self.task.log(
                        logging.WARN,
                        f"Failed to save contact: {contact_dict.get('contact_id')}",
                    )
                except:
                    pass
