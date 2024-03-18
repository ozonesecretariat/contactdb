"""Script to run the kronos event load tasks from cmd line."""

import sys
from django.core.management.base import BaseCommand, CommandParser

from core.models import (
    KronosEvent,
    LoadKronosEventsTask,
    LoadKronosParticipantsTask,
    ResolveAllConflictsTask,
)
from core.utils import ConflictResolutionMethods


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--no-groups",
            action="store_true",
            default=False,
            help="Don't create groups when loading participants",
        )
        parser.add_argument(
            "--resolution",
            choices=ConflictResolutionMethods.values,
            default=ConflictResolutionMethods.SAVE_INCOMING_DATA.value,
            help="What method to use for resolving conflicts",
        )

    def handle(
        self,
        no_groups,
        resolution,
        *args,
        **options,
    ):

        print("Loading events")
        task = LoadKronosEventsTask.objects.create()
        task.run(is_async=False)
        task.refresh_from_db()

        if task.status != "SUCCESS":
            print("Event load task failed!")
            sys.exit(1)

        all_tasks = []
        for event in KronosEvent.objects.all():
            print("Loading participants for", event)
            task = LoadKronosParticipantsTask.objects.create(
                create_groups=not no_groups
            )
            task.kronos_events.add(event)
            all_tasks.append(task)
            task.run(is_async=False)
            task.refresh_from_db()

        if not all(task.status == "SUCCESS" for task in all_tasks):
            print("Not ALL tasks completed successfully.")
            sys.exit(1)

        print("Resolving conflicts using", resolution)
        task = ResolveAllConflictsTask.objects.create(method=resolution)
        task.run(is_async=False)
        task.refresh_from_db()

        if task.status != "SUCCESS":
            print("Conflict resolution task failed!")
            sys.exit(1)
