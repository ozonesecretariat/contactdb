import base64
import logging
from itertools import chain

from django.core.files.base import ContentFile
from django.db import transaction

from common.parsing import CONTACT_MAPPING, REGISTRATION_MAPPING, normalize_title
from core.models import Contact, Country, Organization
from events.kronos import KronosClient
from events.models import (
    Event,
    PriorityPass,
    Registration,
    RegistrationRole,
    RegistrationTag,
)
from events.parsers import KRONOS_STATUS_MAP, KronosParticipantsParser


class ContactPhotosParser:
    def __init__(self, task):
        self.task = task
        self.client = KronosClient()

    def parse_photo_data(self, photo_data):
        """Parse base64 photo data from API response."""
        if not photo_data or "src" not in photo_data:
            return None, None

        src = photo_data["src"]
        if not src.startswith("data:"):
            return None, None

        try:
            header, encoded_data = src.split(",", 1)
            image_data = base64.b64decode(encoded_data)

            # Determine file extension based on Kronos reponse
            if "jpeg" in header or "jpg" in header:
                ext = "jpg"
            elif "png" in header:
                ext = "png"
            elif "gif" in header:
                ext = "gif"
            else:
                # TODO: is this a sane default?
                ext = "jpg"

            return image_data, ext
        except Exception as e:
            self.task.log(logging.ERROR, f"Failed to parse photo data: {e}")
            return None, None

    def import_photo_for_contact(self, contact: Contact):
        """Import photo for a single contact."""
        if not contact.contact_ids:
            self.task.log(logging.WARNING, f"Contact {contact.id} has no Kronos IDs")
            return False

        # If only one Kronos ID, skip metadata lookup
        if len(contact.contact_ids) == 1:
            kronos_id = contact.contact_ids[0]
            try:
                photo_data = self.client.get_contact_photo(kronos_id)
                if not photo_data:
                    self.task.log(
                        logging.INFO, f"No photo found for contact {contact.id}"
                    )
                    return False

                image_data, ext = self.parse_photo_data(photo_data)
                if not image_data:
                    return False

                filename = f"contact_{contact.id}_{kronos_id}.{ext}"
                contact.photo.save(filename, ContentFile(image_data), save=True)

                self.task.log(
                    logging.INFO,
                    f"Photo imported for contact {contact.id} using Kronos ID {kronos_id}",
                )
                return True

            except Exception as e:
                self.task.log(
                    logging.ERROR,
                    f"Error importing photo for contact {contact.id} with Kronos ID {kronos_id}: {e}",
                )
                return False

        # Multiple Kronos IDs - try to find most recent contact with a picture
        contacts_with_dates = []
        for kronos_id in contact.contact_ids:
            try:
                contact_data = self.client.get_contact_data(kronos_id)
                if not contact_data:
                    self.task.log(
                        logging.WARNING,
                        f"No data found for contact {contact.id} with Kronos ID {kronos_id}",
                    )
                    continue

                # Prioritizing updatedOn if available, otherwise using createdOn
                updated_on = contact_data.get("updatedOn")
                created_on = contact_data.get("createdOn")
                contact_date = updated_on or created_on

                if contact_date:
                    contacts_with_dates.append(
                        {
                            "kronos_id": kronos_id,
                            "date": contact_date,
                        }
                    )

            except Exception as e:
                self.task.log(
                    logging.ERROR,
                    f"Error fetching data for contact {contact.id} with Kronos ID "
                    f"{kronos_id}: {e}",
                )

        if not contacts_with_dates:
            self.task.log(
                logging.INFO, f"No Kronos IDs with dates found for contact {contact.id}"
            )
            return False

        # Try each Kronos ID in reverse creation date order, until we find a photo
        contacts_with_dates.sort(key=lambda x: x["date"], reverse=True)

        for contact_with_date in contacts_with_dates:
            kronos_id = contact_with_date["kronos_id"]
            try:
                photo_data = self.client.get_contact_photo(kronos_id)
                if not photo_data:
                    self.task.log(
                        logging.DEBUG,
                        f"No photo found for contact {contact.id} with Kronos ID "
                        f"{kronos_id}",
                    )
                    continue

                image_data, ext = self.parse_photo_data(photo_data)
                if not image_data:
                    continue

                filename = f"contact_{contact.id}_{kronos_id}.{ext}"
                contact.photo.save(filename, ContentFile(image_data), save=True)

                self.task.log(
                    logging.INFO,
                    f"Photo imported for contact {contact.id} using Kronos ID "
                    f"{kronos_id} (date: {contact_with_date['date']})",
                )
                return True

            except Exception as e:
                self.task.log(
                    logging.ERROR,
                    f"Error importing photo for contact {contact.id} with Kronos ID "
                    f"{kronos_id}: {e}",
                )
                continue

        # If we got here, no photos were found for any of the Kronos IDs of the contact
        self.task.log(
            logging.INFO,
            f"No photos found for contact {contact.id}",
        )
        return False

    def import_photos(self, contact_queryset):
        """Import photos for all contacts in supplied queryset."""
        processed = 0
        imported = 0

        for contact in contact_queryset:
            try:
                if self.import_photo_for_contact(contact):
                    imported += 1
                processed += 1
            except Exception as e:
                # Ignoring and moving to next contact
                self.task.log(
                    logging.ERROR, f"Failed to process contact {contact.id}: {e}"
                )
                processed += 1

        self.task.log(
            logging.INFO,
            f"Completed: {imported} photos imported for {processed} contacts",
        )
        return processed, imported


class ContactParser:
    def __init__(self):
        self.client = KronosClient()

    @staticmethod
    def get_or_create_registration_role(role_kronos_enum):
        return RegistrationRole.objects.get_or_create(
            kronos_value=role_kronos_enum,
            defaults={
                "name": role_kronos_enum,
            },
        )[0]

    @staticmethod
    def get_or_create_registration_tags(tags_list):
        if not tags_list:
            return []
        return [
            RegistrationTag.objects.get_or_create(name=tag.strip())[0]
            for tag in tags_list
            if tag and tag.strip()
        ]

    @staticmethod
    def get_priority_pass(code):
        if not code:
            return PriorityPass.objects.create()
        return PriorityPass.objects.get_or_create(code=code)[0]

    @staticmethod
    def create_registration(
        registration_data,
        contact: Contact = None,
        event: Event = None,
        role: RegistrationRole = None,
        tags: list[RegistrationTag] = None,
        priority_pass: PriorityPass = None,
    ) -> Registration | None:
        """
        Create a Registration instance from a Kronos registration
        dictionary.
        """
        if not registration_data:
            return None

        registration_dict = {
            REGISTRATION_MAPPING[key]: value
            for key, value in registration_data.items()
            if key in REGISTRATION_MAPPING
        }

        contact_id = registration_dict.pop("contact_id", None)
        event_id = registration_dict.pop("event_id", None)
        priority_pass_code = registration_dict.pop("priority_pass_code", None)
        status_value = registration_dict.pop("status", None)
        role_value = registration_dict.pop("role", None)
        tags_value = registration_dict.pop("tags", None)

        contact = (
            contact or Contact.objects.filter(id=contact_id).first()
            if contact_id
            else None
        )
        event = (
            event or Event.objects.filter(event_id=event_id).first()
            if event_id
            else None
        )
        status = KRONOS_STATUS_MAP[status_value] if status_value else None
        role = role or ContactParser.get_or_create_registration_role(role_value)
        tags = tags or ContactParser.get_or_create_registration_tags(tags_value)
        priority_pass = priority_pass or ContactParser.get_priority_pass(
            priority_pass_code
        )

        if not (contact and event and role):
            raise ValueError("Contact, event, and role must be provided.")

        registration = Registration.objects.create(
            contact=contact,
            event=event,
            status=status,
            role=role,
            priority_pass=priority_pass,
            **registration_dict,
            organization=contact.organization,
            designation=contact.designation,
            department=contact.department,
        )

        if tags:
            registration.tags.add(*tags)

        return registration

    @staticmethod
    def create_contact(
        contact_data: dict, country=None, organization=None
    ) -> Contact | None:
        """
        Create a Contact instance from a Kronos contact dictionary.
        """
        if not contact_data:
            return None

        country_code = contact_data.pop("country", None)
        organization_id = contact_data.pop("organizationId", None)
        contact_id = contact_data.pop("contactId", None)

        contact_dict = {
            CONTACT_MAPPING[key]: value
            for key, value in contact_data.items()
            if key in CONTACT_MAPPING
        }

        # Update the contact's title
        raw_title = contact_dict.get("title", "")
        english_title, localized_title = normalize_title(raw_title)
        contact_dict["title"] = english_title
        contact_dict["title_localized"] = localized_title

        country = (
            country or Country.objects.get(code=country_code) if country_code else None
        )
        organization = (
            organization or Organization.objects.get(organization_id=organization_id)
            if organization_id
            else None
        )

        langs = KronosParticipantsParser.get_languages(contact_dict.get("notes", ""))

        return Contact.objects.create(
            contact_ids=[contact_id],
            organization=organization,
            country=country,
            **(contact_dict | langs),
        )

    def import_contacts_with_registrations(self, kronos_ids: list) -> list:
        """
        Import contact from Kronos with registrations. Existing contacts
        are deleted and recreated.
        """
        contacts = Contact.objects.filter(contact_ids__overlap=list(kronos_ids))

        # Collect Kronos IDs of contacts that were merged into the
        # main contact.
        all_kronos_ids = set(
            chain.from_iterable(contacts.values_list("contact_ids", flat=True))
        ) | set(kronos_ids)

        new_contacts = []
        with transaction.atomic():
            contacts.delete()

            for kronos_id in all_kronos_ids:
                if not kronos_id:
                    continue

                contact_data = self.client.get_contact_data(kronos_id)
                if not contact_data:
                    continue

                contact_data["contactId"] = kronos_id

                contact = self.create_contact(contact_data)
                new_contacts.append(contact)

                registrations_data = self.client.get_registrations_data(kronos_id)
                if not registrations_data:
                    continue

                for registration_dict in registrations_data:
                    self.create_registration(
                        registration_dict,
                        contact=contact,
                    )

        return new_contacts
