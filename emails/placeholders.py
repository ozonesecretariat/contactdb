import re
from functools import reduce, singledispatch

from django.conf import settings
from django.core.exceptions import ValidationError

from core.models import Contact
from events.models import EventInvitation


@singledispatch
def get_placeholders(obj) -> dict:
    """
    Return placeholders depending on the object type.
    """
    return {}


@get_placeholders.register(Contact)
def _(obj):
    return settings.CKEDITOR_CONTACT_PLACEHOLDERS


@get_placeholders.register(EventInvitation)
def _(obj):
    return settings.CKEDITOR_INVITATION_PLACEHOLDERS


def validate_placeholders(value):
    placeholders = set(re.findall(r"\[\[(.*?)\]\]", value or ""))
    if invalid := placeholders.difference(settings.CKEDITOR_PLACEHOLDERS):
        msg = ", ".join([f"[[{item}]]" for item in invalid])
        raise ValidationError(f"Invalid placeholders: {msg}")


def deep_getattr(obj, attr):
    return reduce(getattr, attr.split("."), obj)


def replace_placeholders(objs: list, text: str) -> str:
    """
    Replace all placeholders in the email content with the actual
    objects values.
    """
    if not objs:
        return text

    objs = filter(None, objs)

    for obj in objs:
        placeholders = get_placeholders(obj)
        placeholder_values = {}
        for placeholder, handles in placeholders.items():
            attr = handles["attr"]
            value = deep_getattr(obj, attr)
            placeholder_values[placeholder] = "" if value is None else value

        # Replace placeholders with values
        for placeholder, value in placeholder_values.items():
            text = text.replace(f"[[{placeholder}]]", str(value))

    return text
