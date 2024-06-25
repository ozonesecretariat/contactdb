"""Script to run the kronos event load tasks from cmd line."""

import sys

from django.core.management.base import BaseCommand

from events.models import (
    Event,
    LoadEventsFromKronosTask,
    LoadParticipantsFromKronosTask,
)


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **options):
        print("Loading events")
        task = LoadEventsFromKronosTask.objects.create()
        task.run(is_async=False)
        task.refresh_from_db()

        if task.status != "SUCCESS":
            print("Event load task failed!")
            sys.exit(1)

        all_tasks = []
        for event in Event.objects.filter(event_id__isnull=False):
            print("Loading participants for", event)
            task = LoadParticipantsFromKronosTask.objects.create(event=event)
            all_tasks.append(task)
            task.run(is_async=False)
            task.refresh_from_db()

        if not all(task.status == "SUCCESS" for task in all_tasks):
            print("Not ALL tasks completed successfully.")
            sys.exit(1)
