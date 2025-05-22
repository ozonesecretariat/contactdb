"""Backfill data for:

- countries
- organization
- organization type
"""

from django.core.management.base import BaseCommand

from core.models import Country, Organization, OrganizationType
from events.kronos import KronosClient


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **options):
        client = KronosClient()
        for country in client.get_countries():
            obj, created = Country.objects.get_or_create(code=country["code"].upper())
            obj.name = ""
            obj.official_name = ""
            obj.clean()
            obj.save()

        for org_type in client.get_org_types():
            OrganizationType.objects.update_or_create(
                organization_type_id=org_type["organizationTypeId"],
                defaults={
                    "acronym": org_type["acronym"],
                    "title": org_type["title"],
                    "description": org_type["description"],
                },
            )

        for event in client.get_meetings():
            event_id = event["eventId"]
            for org_dict in client.get_organizations_for_event(event_id):
                try:
                    org = Organization.objects.get(
                        organization_id=org_dict["organizationId"]
                    )
                except Organization.DoesNotExist:
                    continue

                include_in_invitation = True
                if (
                    org.organization_type.acronym.lower() == "gov"
                    and "#invite" not in org_dict.get("notes", "")
                ):
                    include_in_invitation = False

                org.state = org_dict.get("state")
                org.city = org_dict.get("city")
                org.postal_code = org_dict.get("postalCode")
                org.address = org_dict.get("address")
                org.phones = org_dict.get("phones")
                org.faxes = org_dict.get("faxes")
                org.websites = org_dict.get("webs")
                org.include_in_invitation = include_in_invitation
                org.save()
