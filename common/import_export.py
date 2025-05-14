"""Inspired from https://github.com/django-import-export/django-import-export/issues/318#issuecomment-861813245"""

from django.db.models import QuerySet
from import_export.widgets import ManyToManyWidget


class ManyToManyWidgetWithCreation(ManyToManyWidget):
    """A many-to-many widget that creates any objects that don't already exist."""

    def __init__(self, model, field=None, create=False, **kwargs):
        self.create = create
        super().__init__(model, field=field, **kwargs)

    def clean(self, value, **kwargs):
        # If no value was passed, then we don't have anything to clean.
        if not value:
            return self.model.objects.none()

        # Call the super method. This will return a QuerySet containing any
        # pre-existing objects. Any missing objects will be

        cleaned_value: QuerySet = super().clean(value, **kwargs)

        # Value will be a string separated by `self.separator`. Each entry in
        # the list will be a reference to an object. If the object exists, it will
        # appear in the cleaned_value results. If the number of objects in the
        # cleaned_value results matches the number of objects in the delimited list,
        # then all objects already exist, and we can just return those results.

        object_list = value.split(self.separator)
        if len(cleaned_value.all()) == len(object_list):
            return cleaned_value

        # If we are creating new objects, then loop over each object in the list and
        # use get_or_create to, um, get or create the object.

        if self.create:
            for object_value in object_list:
                _instance, _new = self.model.objects.get_or_create(
                    **{self.field: object_value}
                )

        # Use `filter` to re-locate all the objects in the list.
        return self.model.objects.filter(**{f"{self.field}__in": object_list})
