"""
Script to update event registrations fields (organization, designation,
and department) using participant data from Kronos.
"""

from django.core.management.base import BaseCommand

from core.models import Contact, Organization
from events.kronos import KronosClient
from events.models import Event, Registration


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **options):
        client = KronosClient()
        events = Event.objects.filter(event_id__isnull=False)

        self.stdout.write("Updating registrations from Kronos...")

        updated_count = 0
        for event in events:
            self.stdout.write(f"Processing event: {event}")
            for contact_dict in client.get_participants(event.event_id):
                contact_id = contact_dict["contactId"]

                designation = contact_dict.get("designation", "")
                department = contact_dict.get("department", "")

                org_dict = contact_dict.get("organization", {})
                organization = (
                    Organization.objects.filter(
                        organization_id=org_dict.get("organizationId", None)
                    ).first()
                    if org_dict
                    else None
                )

                contact = (
                    Contact.objects.filter(contact_ids__contains=[contact_id])
                    .prefetch_related("conflicting_contacts")
                    .first()
                )

                for registration in contact_dict["registrationStatuses"]:
                    if registration is None:
                        continue

                    event = Event.objects.filter(
                        event_id=registration["eventId"]
                    ).first()
                    registration = Registration.objects.filter(
                        contact=contact,
                        event=event,
                    ).first()

                    if not registration:
                        continue

                    registration.organization = organization
                    registration.designation = designation
                    registration.department = department
                    registration.save()
                    updated_count += 1
                    self.stdout.write(f"Updated registration for {registration}.")
        self.stdout.write(f"Updated {updated_count} registrations from Kronos.")
