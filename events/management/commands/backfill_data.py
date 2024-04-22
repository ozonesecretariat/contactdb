"""Backfill data for:

- countries
- organization
"""

from django.core.management.base import BaseCommand
from core.models import Country, OrganizationType
from events.kronos import KronosClient


class Command(BaseCommand):
    help = __doc__

    def handle(self, *args, **options):
        client = KronosClient()
        for country in client.get_countries():
            obj, created = Country.objects.get_or_create(code=country["code"])
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
