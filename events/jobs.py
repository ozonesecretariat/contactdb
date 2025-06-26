import logging

from django_task.job import Job

from events.models import Registration
from events.parsers import (
    KronosEventsParser,
    KronosOrganizationsParser,
    KronosParticipantsParser,
)


class LoadEventsFromKronos(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Loading events from Kronos")

        parser = KronosEventsParser(task=task)
        count_created, count_updated = parser.parse_event_list()
        task.description = (
            f"Imported {count_created} new events and "
            f"updated {count_updated} existing events."
        )
        task.save()

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Events loaded")


class LoadParticipantsFromKronos(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Loading participants from Kronos")
        parser = KronosParticipantsParser(task=task)
        parser.parse_contact_list()
        task.save()

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Participants loaded")


class LoadOrganizationsFromKronos(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Loading organizations from Kronos")
        parser = KronosOrganizationsParser(task=task)
        parser.parse_organizations_list()
        task.save()

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Organizations loaded")


def resend_confirmation_email(registration_id):
    try:
        registration = Registration.objects.get(id=registration_id)
    except Registration.DoesNotExist:
        # Deleted while in the queue
        return

    registration.send_confirmation_email()
