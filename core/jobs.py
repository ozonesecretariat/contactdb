import logging
import string
import pycountry
import requests
from django.conf import settings
from django.db.models import Q, QuerySet
from django.utils.text import smart_split
from django_task.job import Job
from core.models import Country, Organization

punctuation_translate = {ord(c): " " for c in string.punctuation}


class ImportFocalPoints(Job):
    @classmethod
    def _search_pycountry(cls, name):
        results = pycountry.countries.search_fuzzy(name)
        if len(results) > 1:
            raise LookupError(f"Multiple countries found for {name}: {results}")
        return results[0]

    @classmethod
    def get_names_to_search(cls, name):
        name = name.strip()

        name_no_punctuation = name.translate(punctuation_translate)
        names_to_search = [name, name_no_punctuation, *smart_split(name_no_punctuation)]
        return names_to_search

    @classmethod
    def search_multiple(cls, querysets: [QuerySet], name: str, fields: [str]):
        model = querysets[0].model
        for queryset in querysets:
            try:
                return cls.search_names(queryset, name, fields)
            except model.DoesNotExist:
                pass
        raise LookupError(f"Unable to find {model.__name__} for: {name}")

    @classmethod
    def search_names(cls, original_query: QuerySet, name: str, fields: [str]):
        name = name.strip()
        if not name:
            return

        model = original_query.model

        for field in fields:
            try:
                return original_query.get(**{field: name})
            except (model.DoesNotExist, model.MultipleObjectsReturned):
                continue

        names_to_search = cls.get_names_to_search(name)
        for name in names_to_search:
            query = original_query.all()
            for part in smart_split(name):
                filter_combined = None
                for field in fields:
                    filter_q = Q(**{f"{field}__icontains": part})
                    if not filter_combined:
                        filter_combined = filter_q
                    else:
                        filter_combined |= filter_q

                query = query.filter(filter_combined)

            try:
                return query.get()
            except (model.DoesNotExist, model.MultipleObjectsReturned) as e:
                print("Not found for name", name, e)
                continue
        raise model.DoesNotExist

    @classmethod
    def get_country(cls, name: str):
        try:
            return cls.search_names(
                Country.objects.all(),
                name,
                ["code", "name", "official_name"],
            )
        except Country.DoesNotExist:
            pass

        for to_search in cls.get_names_to_search(name):
            try:
                country = cls._search_pycountry(to_search)
            except LookupError:
                continue

            return Country.objects.get_or_create(
                code=country.alpha_2,
                defaults={
                    "name": country.name,
                },
            )[0]
        raise LookupError(f"Unable to find country for: {name}")

    @classmethod
    def get_organization(cls, name, country):
        return cls.search_multiple(
            [
                Organization.objects.all(),
                Organization.objects.filter(country=country),
            ],
            name,
            ["name"],
        )

    @classmethod
    def process_contact(cls, item):
        party = cls.get_country(item["party"])
        country = cls.get_country(item["country"])
        org = cls.get_organization(item["organisation"], country)

    @classmethod
    def execute(cls, job, task):
        url = settings.FOCAL_POINT_ENDPOINT
        task.log(logging.INFO, "Loading focal points from: %s", url)

        resp = requests.get(url)
        resp.raise_for_status()
        for contact in resp.json():
            cls.process_contact(contact)

    @staticmethod
    def on_complete(job, task):
        task.log(logging.INFO, "Focal points imported")
