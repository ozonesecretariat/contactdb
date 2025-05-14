"""Script to run import focal points from cmd line."""

from django.core.management.base import BaseCommand

from core.models import ImportFocalPointsTask


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **options):
        task = ImportFocalPointsTask.objects.create()
        task.run(is_async=False)
