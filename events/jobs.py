import logging

from django_task.job import Job
from django_task.utils import get_model_from_id

from events.models import Registration
from events.parsers import (
    KronosEventsParser,
    KronosOrganizationsParser,
    KronosParticipantsParser,
)

logger = logging.getLogger(__name__)


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
    if registration := get_model_from_id(Registration, registration_id):
        registration.send_confirmation_email()
    else:
        logger.warning(
            "Could not find registration %s to resend confirmation email",
            registration_id,
        )
