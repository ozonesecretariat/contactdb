from django.core.management.base import BaseCommand, CommandParser

from core.parsers import ContactParser


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--kronos-ids",
            nargs="+",
            type=str,
            required=True,
            help="List of Kronos contact IDs to import.",
        )

    def handle(self, kronos_ids: list, *args, **options):
        contact_parser = ContactParser()
        contacts = contact_parser.import_contacts_with_registrations(kronos_ids)

        self.stdout.write(f"Imported {len(contacts)} contact(s):")
        for contact in contacts:
            contact_id = contact.contact_ids[0] if contact.contact_ids else "N/A"
            registration_count = contact.registrations.count()

            self.stdout.write(
                f"{contact_id} {contact.full_name} ({registration_count} registrations)"
            )
