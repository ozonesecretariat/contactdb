import pycountry
from django.db.models import Q, QuerySet, TextField
from django.db.models.functions import Cast
from django.utils.text import smart_split

from common.parsing import remove_punctuation
from core.models import Country, Organization

# Countries whose names cannot be deduced from the official name via fuzzy search.
COUNTRY_MAP = {
    "The Islamic Emirate of Afghanistan": "AF",
}


def get_names_to_search(name):
    name = name.strip()
    return [name, remove_punctuation(name)]


def search_multiple(querysets: [QuerySet], name: str, fields: [str]):
    model = querysets[0].model
    for queryset in querysets:
        try:
            return search_names(queryset, name, fields)
        except model.DoesNotExist:
            pass
    raise LookupError(f"Unable to find {model.__name__} for: {name}")


def search_names(original_query: QuerySet, name: str, fields: [str]):
    name = (name or "").strip()
    if not name:
        return None

    model = original_query.model

    for field in fields:
        try:
            return original_query.annotate(
                _search_field=Cast(field, output_field=TextField())
            ).get(_search_field=name)
        except (model.DoesNotExist, model.MultipleObjectsReturned):
            continue

    names_to_search = get_names_to_search(name)
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
        except (model.DoesNotExist, model.MultipleObjectsReturned):
            continue
    raise model.DoesNotExist


def search_pycountry(name):
    results = pycountry.countries.search_fuzzy(name)
    if len(results) > 1:
        raise LookupError(f"Multiple countries found for {name}: {results}")
    return results[0]


def get_country(names: str | list[str]):
    if not isinstance(names, list):
        names = [names]

    for name in names:
        name = COUNTRY_MAP.get(name, name)
        try:
            return search_names(
                Country.objects.all(),
                name,
                ["code", "name", "official_name"],
            )
        except Country.DoesNotExist:
            pass

        for to_search in get_names_to_search(name):
            try:
                country = search_pycountry(to_search)
            except LookupError:
                continue

            return Country.objects.get_or_create(
                code=country.alpha_2,
                defaults={
                    "name": country.name,
                },
            )[0]
    raise LookupError(f"Unable to find country for: {names}")


def get_organization(names: str | list[str], party, country):
    if not isinstance(names, list):
        names = [names]

    querysets = []
    if country:
        querysets.append(Organization.objects.filter(country=country))
        querysets.append(Organization.objects.filter(government=country))
    if party:
        querysets.append(Organization.objects.filter(country=party))
        querysets.append(Organization.objects.filter(government=party))

    if querysets:
        try:
            for name in names:
                return search_multiple(querysets, name, ["name", "alt_names"])
        except LookupError:
            pass

    return Organization.objects.create(
        name=names[0].strip(), acronym="", country=country, government=party
    )
