import re

from django.conf import settings
from django.core.exceptions import ValidationError


def find_placeholders(value):
    return set(re.findall(r"\[\[([\w-]{1,50})\]\]", value or ""))


def validate_placeholders(value):
    placeholders = find_placeholders(value)
    if invalid := placeholders.difference(settings.CKEDITOR_PLACEHOLDERS):
        msg = ", ".join([f"[[{item}]]" for item in invalid])
        raise ValidationError(f"Invalid placeholders: {msg}")
