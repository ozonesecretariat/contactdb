import logging
from copy import copy

from django_task.job import Job

from core.models import ResolveConflict
from common.utils import ConflictResolutionMethods, update_object


class ResolveAllConflicts(Job):
    @classmethod
    def execute(cls, job, task):
        task.log(logging.INFO, "Resolving conflicts")
        if task.method == ConflictResolutionMethods.KEEP_OLD_DATA:
            ResolveConflict.objects.all().delete()
        elif task.method == ConflictResolutionMethods.SAVE_INCOMING_DATA:
            incoming_contacts = ResolveConflict.objects.select_related(
                "existing_contact"
            ).all()
            for incoming_contact in incoming_contacts:
                task.log(
                    logging.INFO,
                    f"Resolving conflict for {incoming_contact}",
                )
                cls.save_incoming_data(incoming_contact)

    @staticmethod
    def save_incoming_data(incoming_contact):
        record = incoming_contact.existing_contact
        update_values = copy(dict(vars(incoming_contact)))
        update_values.pop("existing_contact_id")
        update_values.pop("id")
        update_object(record, update_values)
        ResolveConflict.objects.filter(pk=incoming_contact.id).first().delete()

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Conflicts resolved")
