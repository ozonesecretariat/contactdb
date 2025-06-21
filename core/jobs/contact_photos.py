import logging

from django_task.job import Job

from core.models import Contact
from core.parsers import ContactPhotosParser


class ImportContactPhotos(Job):
    @staticmethod
    def execute(job, task):
        task.log(logging.INFO, "Loading contact photos from Kronos")

        parser = ContactPhotosParser(task)

        # Only keeping the contacts that have Kronos id's
        contacts_query = Contact.objects.exclude(contact_ids__isnull=True).exclude(
            contact_ids=[]
        )

        if task.contact_ids:
            contacts_query = contacts_query.filter(id__in=task.contact_ids)

        # If overwrite not enabled, skipping contacts with existing photos
        if not task.overwrite_existing:
            contacts_query = contacts_query.filter(photo__isnull=True)

        processed, imported = parser.import_photos(contacts_query)

        task.description = f"Processed {processed} contacts, imported {imported} photos"
        task.save()

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Contact photos loaded")
