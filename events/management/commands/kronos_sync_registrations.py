"""
Script to update event registrations fields (organization, designation,
and department) using participant data from Kronos.
"""

from django.core.management.base import BaseCommand

from core.models import Organization
from events.kronos import KronosClient
from events.models import Event, Registration


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **options):
        client = KronosClient()
        events = Event.objects.filter(event_id__isnull=False)

        self.stdout.write("Updating registrations from Kronos...")

        for event in events:
            updated_count = 0
            batch = []
            for contact_dict in client.get_participants(event.event_id):
                contact_id = contact_dict["contactId"]

                designation = contact_dict.get("designation", "")
                department = contact_dict.get("department", "")

                org_id = contact_dict.get("organization", {}).get(
                    "organizationId", None
                )
                organization = (
                    Organization.objects.filter(organization_id=org_id).first()
                    if org_id
                    else None
                )

                registration = (
                    Registration.objects.select_related("contact")
                    .filter(
                        contact__contact_ids__contains=[contact_id],
                        event=event,
                    )
                    .first()
                )

                if not registration:
                    continue

                registration.organization = organization
                registration.designation = designation
                registration.department = department
                batch.append(registration)

                updated_count += 1

            if batch:
                Registration.objects.bulk_update(
                    batch, ["organization", "designation", "department"]
                )
                self.stdout.write(
                    f"Updated {updated_count} registrations from {event}."
                )
