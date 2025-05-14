"""Script to run import legacy contacts from cmd line."""

import argparse
import sys

from django.core.files import File
from django.core.management.base import BaseCommand, CommandParser

from core.models import ImportLegacyContactsTask


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "json_file",
            nargs="?",
            type=argparse.FileType("r"),
            default=sys.stdin,
        )
        parser.add_argument(
            "-c",
            "--clear",
            action="store_true",
            default=False,
        )

    def handle(self, json_file, clear, *args, **options):
        task = ImportLegacyContactsTask.objects.create(
            json_file=File(json_file),
            clear_previous=clear,
        )
        task.run(is_async=False)
