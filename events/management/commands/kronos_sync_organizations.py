"""Script to run the kronos organization load task from cmd line."""

import sys

from django.core.management.base import BaseCommand

from events.models import LoadOrganizationsFromKronosTask


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **options):
        self.stderr.write("Loading organizations")
        task = LoadOrganizationsFromKronosTask.objects.create()
        task.run(is_async=False)
        task.refresh_from_db()

        if task.status != "SUCCESS":
            self.stderr.write("Organizations load task failed!")
            sys.exit(1)
