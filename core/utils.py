from django.db import models
from django.utils.translation import gettext_lazy as _


def check_field(field, subfield):
    if subfield == "role" or subfield == "dateOfBirth":
        return field[subfield] if subfield in field else None
    if subfield == "tags":
        return field[subfield] if subfield in field else []
    return field[subfield] if subfield in field else ""


class ConflictResolutionMethods(models.TextChoices):
    KEEP_OLD_DATA = "keep_old_data", _("Keep old data")
    SAVE_INCOMING_DATA = "save_incoming_data", _("Save incoming data")


def update_object(obj, update_dict):
    for key, value in update_dict.items():
        setattr(obj, key, value)
    obj.save()
