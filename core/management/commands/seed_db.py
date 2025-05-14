import sys

from django.conf import settings
from django.core.management import BaseCommand, call_command
from redis import StrictRedis


class Command(BaseCommand):
    help = "Seed DB for E2E tests"

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_true",
            help="Do not prompt for any user input",
            default=False,
        )

    def clear_queue(self):
        db = StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        db.flushall()

    def handle(self, *args, noinput=False, **options):
        if not noinput:
            self.stderr.write(
                "This will IRREVERSIBLY DESTROY all data currently in the  database! "
                "Are you sure you want to continue?",
                end=" ",
            )
            if input("[Y/n] ") != "Y":
                sys.exit(1)

        call_command("flush", "--noinput")
        self.clear_queue()

        call_command("load_fixtures", "initial")
        # Create users / password:
        #  - admin@example.com / admin
        call_command("load_fixtures", "test")
