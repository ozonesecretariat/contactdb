import logging

from django.conf import settings
from django.core.management import BaseCommand
from django.core.management import call_command

from accounts.models import Role, User
from events.models import RegistrationRole, RegistrationStatus, RegistrationTag


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Load fixtures data"

    # Order is important
    FIXTURES = {
        "initial": (
            # auth
            Role,
            # events
            RegistrationTag,
            RegistrationRole,
            RegistrationStatus,
        ),
        "test": (
            # User
            User,
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
