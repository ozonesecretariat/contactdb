from django.core.management.base import BaseCommand, CommandParser

from core.parsers import ContactParser


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--kronos-ids",
            nargs="+",
            type=str,
            help="List of contact IDs to import.",
        )

    def handle(self, kronos_ids: list, *args, **options):
        contact_parser = ContactParser()
        contacts = contact_parser.import_contacts_with_registrations(kronos_ids)

        self.stdout.write(f"Found {len(contacts)} contacts to import:")
        for contact in contacts:
            self.stdout.write(
                f"{contact.contact_ids[0]} {contact.full_name} "
                f"with {contact.registrations.count()} registrations",
            )
