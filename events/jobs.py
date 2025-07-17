import logging

from django_task.job import Job
from django_task.utils import get_model_from_id

from events.models import PriorityPass
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


def send_priority_pass_status_emails(priority_pass_id):
    if priority_pass := get_model_from_id(PriorityPass, priority_pass_id):
        priority_pass.send_confirmation_email()
        priority_pass.send_revoke_email()
    else:
        logger.warning(
            "Could not find priority pass %s to end confirmation email",
            priority_pass_id,
        )
