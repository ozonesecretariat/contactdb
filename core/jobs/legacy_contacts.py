import json
import logging

from django_task.job import Job

from common import fuzzy_search
from common.parsing import parse_list
from core.models import Contact, ContactGroup


class ImportLegacyContacts(Job):
    @classmethod
    def get_addresses(cls, item: dict):
        result = []
        for key, value in item.items():
            if key.lower().startswith("address line") and (value := value.strip()):
                result.append(value)
        return result

    @classmethod
    def process_contact(cls, item: dict):
        country = fuzzy_search.get_country(
            [
                item.get("Country_code"),
                item.get("Country Name"),
                item.get("Address Country"),
            ]
        )

        contact = Contact.objects.create(
            country=country,
            organization=None,
            address="\n".join(cls.get_addresses(item)),
            city=item.get("Address City", ""),
            emails=parse_list(item.get("E-Mail", "")),
            email_ccs=parse_list(item.get("Bouncing-Email", "")),
            faxes=parse_list(item.get("Fax", "")),
            designation=item.get("Functional Title", ""),
            org_head=item.get("Head of Organization", False),
            last_name=item.get("NameLast", ""),
            first_name=item.get("NameOthers", ""),
            title=item.get("NameTitle", ""),
            primary_lang=item.get("Primary Language", ""),
            second_lang=item.get("Second Language", ""),
            honorific=item.get("Salutation", ""),
            phones=parse_list(item.get("Telephone", "")),
        )
        contact.add_to_group("Legacy contacts")
        return contact

    @classmethod
    def execute(cls, job, task):
        if task.clear_previous:
            task.log(logging.INFO, "Removing previous legacy contacts from")
            details = (
                ContactGroup.objects.get(name="Legacy contacts").contacts.all().delete()
            )
            task.log(logging.INFO, "Removed old contacts: %s", details)

        task.log(logging.INFO, "Loading legacy contacts from file: %s", task.json_file)
        with task.json_file.open() as fp:
            contacts = json.load(fp)

        for item in contacts:
            contact = cls.process_contact(item)
            task.log(
                logging.INFO,
                "Contact with legacy id %s created: %r",
                item["AddressID"],
                contact,
            )
        task.description = f"Contacts created={len(contacts)}"
        task.save()

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Legacy contacts imported")
