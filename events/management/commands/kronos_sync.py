"""Script to run the kronos event load tasks from cmd line."""

import sys
from django.core.management.base import BaseCommand, CommandParser

from core.models import (
    ResolveAllConflictsTask,
)
from events.models import (
    Event,
    LoadEventsFromKronosTask,
    LoadParticipantsFromKronosTask,
)
from common.utils import ConflictResolutionMethods


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "-ng",
            "--no-groups",
            action="store_true",
            default=False,
            help="Don't create groups when loading participants",
        )
        parser.add_argument(
            "-nr",
            "--no-resolve-conflicts",
            action="store_true",
            default=False,
            help="Don't resolve any of the conflicts.",
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
        no_resolve_conflicts,
        resolution,
        *args,
        **options,
    ):

        print("Loading events")
        task = LoadEventsFromKronosTask.objects.create()
        task.run(is_async=False)
        task.refresh_from_db()

        if task.status != "SUCCESS":
            print("Event load task failed!")
            sys.exit(1)

        all_tasks = []
        for event in Event.objects.all():
            print("Loading participants for", event)
            task = LoadParticipantsFromKronosTask.objects.create(
                create_groups=not no_groups,
                event=event,
            )
            all_tasks.append(task)
            task.run(is_async=False)
            task.refresh_from_db()

        if not all(task.status == "SUCCESS" for task in all_tasks):
            print("Not ALL tasks completed successfully.")
            sys.exit(1)

        if not no_resolve_conflicts:
            print("Resolving conflicts using", resolution)
            task = ResolveAllConflictsTask.objects.create(method=resolution)
            task.run(is_async=False)
            task.refresh_from_db()

        if task.status != "SUCCESS":
            print("Conflict resolution task failed!")
            sys.exit(1)
