import logging
from django.db.models import Q
from django_task.job import Job
from events import kronos
from core.models import Contact, ContactGroup
from events.parsers import KronosEventsParser, KronosParticipantsParser


class LoadEventsFromKronos(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Loading events from Kronos")

        kronos_client = kronos.Client()
        kronos_client.login()
        response = kronos_client.get_meetings()
        parser = KronosEventsParser(task=task)
        count_created, count_updated = parser.parse_event_list(response["records"])
        task.description = f"Imported {count_created} new events and updated {count_updated} existing events."
        task.save()

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Events loaded")


class LoadParticipantsFromKronos(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Loading participants from Kronos")
        kronos_client = kronos.Client()
        kronos_client.login()

        event = task.event

        parser = KronosParticipantsParser(task=task)
        response = kronos_client.get_participants(event.event_id)
        parser.parse_contact_list(response.get("records"))
        task.save()

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Participants loaded")
