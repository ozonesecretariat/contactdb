import logging
from copy import copy

from django.db import connection
from django_task.job import Job
from django.core.mail import send_mail, send_mass_mail

from core import kronos
from core.models import TemporaryContact, EmailTag
from core.parsers import KronosEventsParser, KronosParticipantsParser
from core.utils import ConflictResolutionMethods, update_object


class SendMailJob(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Sending email")
        task.email.send()
        task.email.save()


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


class ResolveAllConflicts(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Resolving conflicts")
        try:
            if task.method == ConflictResolutionMethods.KEEP_OLD_DATA:
                TemporaryContact.objects.all().delete()
            elif task.method == ConflictResolutionMethods.SAVE_INCOMING_DATA:
                incoming_contacts = TemporaryContact.objects.select_related(
                    "record"
                ).all()
                for incoming_contact in incoming_contacts:
                    try:
                        task.log(
                            logging.INFO,
                            f"Resolving conflict for {incoming_contact}",
                        )
                        record = incoming_contact.record
                        update_values = copy(vars(incoming_contact))
                        update_values.pop("record_id")
                        update_values.pop("id")
                        update_object(record, update_values)
                        TemporaryContact.objects.filter(
                            pk=incoming_contact.id
                        ).first().delete()
                    except Exception as e:
                        task.log(logging.ERROR, e)

        except Exception as e:
            task.log(logging.ERROR, e)

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Conflicts resolved")
