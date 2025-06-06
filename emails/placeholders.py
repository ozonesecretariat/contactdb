import re
from functools import singledispatch
from typing import Any

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


def deep_getattr(obj, attr, default=None):
    """Get nested attribute"""
    try:
        for name in attr.split("__"):
            obj = getattr(obj, name)
        return obj
    except AttributeError:
        if isinstance(default, str) and default:
            # Try fallback path if provided
            return deep_getattr(obj, default, None)
        return default


def replace_placeholders(objs: list[Any], text: str) -> str:
    """
    For each object in `objs`, replace [[placeholder]] tags in `text`
    with the corresponding value, as defined by `get_placeholders`.

    If `objs` is empty, returns the original text unchanged.
    """
    if not objs or not text:
        return text

    objs = filter(None, objs)

    for obj in objs:
        # Get placeholders for the object type
        placeholders = get_placeholders(obj)

        placeholder_values = {}
        for placeholder, handles in placeholders.items():
            attr = handles["attr"]
            fallback = handles.get("fallback")
            value = deep_getattr(obj, attr, fallback)
            placeholder_values[placeholder] = "" if value is None else value

        # Replace placeholders with values
        for placeholder, value in placeholder_values.items():
            text = text.replace(f"[[{placeholder}]]", str(value))

    return text
