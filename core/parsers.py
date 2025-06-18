import base64
import logging

from django.core.files.base import ContentFile

from core.models import Contact
from events.kronos import KronosClient


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
                    "{kronos_id} (date: {contact_with_date['date']})",
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
