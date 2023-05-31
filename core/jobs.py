import json
import logging
import time

from django_task.job import Job
from django.core.mail import send_mail

from core import kronos
from core.parsers import KronosEventsParser, KronosParticipantsParser
from core.temp_models import create_temporary_table, TemporaryContact


class SendMailJob(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Sending email to: %s", task.recipient)

        send_mail(
            task.subject.strip(),
            task.message,
            None,
            [task.recipient],
        )


class LoadKronosEvents(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Loading events from Kronos")

        try:
            kronos_client = kronos.Client()
            kronos_client.login()
            response = kronos_client.get_meetings()
            parser = KronosEventsParser(task=task)
            count_created, count_updated = parser.parse_event_list(response["records"])
            task.description = f"Imported {count_created} new events and updated {count_updated} existing events."
            task.save()
        except Exception as e:
            task.log(logging.ERROR, e)

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Events loaded")


class LoadKronosParticipants(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Loading participants from Kronos")
        try:
            kronos_client = kronos.Client()
            kronos_client.login()
            event_ids = task.kronos_events.values_list("event_id", flat=True)
            response = kronos_client.get_participants(event_ids)
            create_temporary_table()
            parser = KronosParticipantsParser(task=task)
            parser.parse_contact_list(response.get("records"))
            task.description = (
                f"Imported participants from the next events: {' '.join(event_ids)}."
            )
            task.save()

        except Exception as e:
            task.log(logging.ERROR, e)

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Participants loaded")
