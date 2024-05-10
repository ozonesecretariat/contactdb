import logging
import requests
from django.conf import settings
from django_task.job import Job
from common import fuzzy_search
from common.scheduler import cron
from core.models import Contact, ImportFocalPointsTask
from common.parsing import parse_list

TITLES = {
    "Abog",
    "Amb",
    "Dr",
    "Eng",
    "Engr",
    "Ing",
    "Ir",
    "Lic",
    "MP",
    "Miss",
    "Mme",
    "Mr",
    "Mrs",
    "Ms",
    "Rev",
    "Sr",
    "Sra",
    "H.E",
    "H.E",
    "Honorable",
}
KNOWN_TITLES = TITLES.union({_t + "." for _t in TITLES})


@cron("20 0 * * *")
def trigger_import_focal_point():
    task = ImportFocalPointsTask.objects.create()
    task.run(is_async=True)


class ImportFocalPoints(Job):
    @classmethod
    def process_contact(cls, item):
        party = fuzzy_search.get_country(item["party"])
        country = fuzzy_search.get_country(item["country"])
        org = fuzzy_search.get_organization(item["organisation"], party, country)

        try:
            first_name, last_name = item["name"].rsplit(None, 1)
        except ValueError:
            first_name, last_name = "", item["name"]

        try:
            title, other = first_name.split(None, 1)
            assert title in KNOWN_TITLES
            first_name = other
        except (ValueError, AssertionError):
            title = ""

        contact = Contact.objects.create(
            focal_point_ids=[item["id"]],
            title=title,
            first_name=first_name,
            last_name=last_name,
            organization=org,
            country=party or country,
            designation=item["designation"],
            phones=parse_list(item["tel"]),
            emails=parse_list(item["email"]),
            faxes=parse_list(item["fax"]),
            address=item["address"],
            city=item["city"],
        )

        contact.add_to_group("Focal point")
        if item["is_licensing_system"]:
            contact.add_to_group("FPLS")
        if item["is_national"]:
            contact.add_to_group("NFP")

        return contact

    @classmethod
    def execute(cls, job, task):
        url = settings.FOCAL_POINT_ENDPOINT
        task.log(logging.INFO, "Loading focal points from: %s", url)

        resp = requests.get(url)
        resp.raise_for_status()

        created, skipped = 0, 0
        for item in resp.json():
            focal_id = item["id"]
            try:
                contact = Contact.objects.get(focal_point_ids__contains=[focal_id])
                task.log(
                    logging.INFO,
                    "Focal point with id %s already exists: %s",
                    focal_id,
                    contact,
                )
                skipped += 1
                continue
            except Contact.DoesNotExist:
                pass

            contact = cls.process_contact(item)
            created += 1
            task.log(
                logging.INFO,
                "Contact with focal point %s created: %s",
                focal_id,
                contact,
            )
        task.description = f"Contacts created={created}; skipped={skipped}"
        task.save()

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Focal points imported")
