import logging

from django.conf import settings
from django.core.management import BaseCommand, call_command

from accounts.models import Role, User
from core.models import (
    Contact,
    ContactGroup,
    Country,
    ImportFocalPointsTask,
    ImportLegacyContactsTask,
    Organization,
    OrganizationType,
    Region,
    ResolveConflict,
    Subregion,
)
from emails.models import Email, EmailTemplate, SendEmailTask
from events.models import (
    Event,
    EventGroup,
    EventInvitation,
    LoadEventsFromKronosTask,
    LoadParticipantsFromKronosTask,
    Registration,
    RegistrationRole,
    RegistrationTag,
)

logger = logging.getLogger("contactdb")


class Command(BaseCommand):
    help = "Load fixtures data"

    # Order is important
    FIXTURES = {
        "initial": (
            # Accounts
            Role,
            # core
            Region,
            Subregion,
            Country,
            ContactGroup,
            OrganizationType,
            # Events
            RegistrationTag,
            RegistrationRole,
        ),
        "test": (
            # User
            User,
            # Core
            Organization,
            ContactGroup,
            Contact,
            ResolveConflict,
            ImportFocalPointsTask,
            ImportLegacyContactsTask,
            # Events
            EventGroup,
            Event,
            EventInvitation,
            LoadEventsFromKronosTask,
            LoadParticipantsFromKronosTask,
            Registration,
            # Email
            EmailTemplate,
            Email,
            SendEmailTask,
        ),
    }

    def add_arguments(self, parser):
        parser.add_argument("fixture_type", choices=("initial", "test"))
        parser.add_argument(
            "-e",
            "--exclude",
            action="append",
            default=[],
            help="Exclude fixtures from the list",
        )
        parser.add_argument(
            "--dump",
            action="store_true",
            default=False,
            help="Dump the data back to the fixtures instead of loading it in the DB",
        )

    def handle(self, fixture_type, *args, exclude, dump=False, **options):
        logging.basicConfig()
        for model in self.FIXTURES[fixture_type]:
            opt = model._meta
            name = opt.model_name
            path = settings.MAIN_FIXTURES_DIR / fixture_type / f"{name}.json"

            if name in exclude:
                continue

            if dump:
                logger.info("Dumping fixtures: %s", path)
                call_command(
                    "dumpdata",
                    "--indent",
                    "2",
                    "-o",
                    str(path),
                    "--natural-foreign",
                    "--natural-primary",
                    f"{opt.app_label}.{name}",
                )
            else:
                logger.info("Loading fixtures: %s", path)
                call_command("loaddata", path)
