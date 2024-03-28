import re

import pycountry
from django.conf import settings
from django.db import models


def check_field(field, subfield):
    if subfield == "role" or subfield == "dateOfBirth":
        return field[subfield] if subfield in field else None
    if subfield == "tags":
        return field[subfield] if subfield in field else []
    return field[subfield] if subfield in field else ""


class ConflictResolutionMethods(models.TextChoices):
    KEEP_OLD_DATA = "keep_old_data", "Keep old data"
    SAVE_INCOMING_DATA = "save_incoming_data", "Save incoming data"


def update_object(obj, update_dict):
    for key, value in update_dict.items():
        setattr(obj, key, value)
    obj.save()


def check_diff(obj, dictionary):
    for key, value in dictionary.items():
        if getattr(obj, key) != value:
            return True
    return False


def get_relative_image_urls(email_body):
    img_tag_pattern = r'<img.*?src="(.*?)"'
    relative_image_urls = re.findall(img_tag_pattern, email_body)
    return list(set(relative_image_urls))


def replace_relative_image_urls(email_body):
    relative_urls = get_relative_image_urls(email_body)
    domain = settings.PROTOCOL + settings.BACKEND_HOST[0]
    for url in relative_urls:
        absolute_url = domain + url
        email_body = email_body.replace(url, absolute_url)

    return email_body


def get_country_code(country_name):
    try:
        country = pycountry.countries.get(name=country_name)
        return country.alpha_2
    except (AttributeError, KeyError):
        return ""
