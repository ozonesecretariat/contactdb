from collections import Counter

from django.contrib.admin import SimpleListFilter
from django.contrib.admin.widgets import AdminTextInputWidget
from django.contrib.postgres.fields import ArrayField as DjangoArrayField
from django.contrib.postgres.forms.array import SimpleArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Func
from django.forms import Widget


class ArrayFieldWidget(Widget):
    """Widget that includes one input for each entry of the array."""

    template_name = "admin/widgets/array_field.html"

    def render(self, name, value, attrs=None, renderer=None):
        # If no value yet, initialize with one empty
        value = value or [""]
        widgets = []
        widget = AdminTextInputWidget(attrs=self.attrs)
        for item in value:
            widgets.append(widget.render(name, item, attrs=attrs, renderer=renderer))

        return self._render(
            self.template_name,
            {
                "widgets": widgets,
                "template_widget": widget.render(
                    name, "", attrs=attrs, renderer=renderer
                ),
                "name": name,
            },
            renderer=renderer,
        )

    def value_from_datadict(self, data, files, name):
        return [value for value in data.getlist(name) if value.strip()]


class CustomSimpleArrayField(SimpleArrayField):
    def prepare_value(self, value):
        # Return value as an array instead of string as our custom widget
        # knows how to handle that.
        return value


class ArrayField(DjangoArrayField):
    """Custom array field that has better admin widget."""

    def __init__(self, *args, allow_duplicates=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_duplicates = allow_duplicates

    def formfield(self, **kwargs):
        kwargs.setdefault("form_class", CustomSimpleArrayField)
        kwargs.setdefault("widget", ArrayFieldWidget)
        return super().formfield(**kwargs)

    def run_validators(self, value):
        super().run_validators(value)
        if self.allow_duplicates:
            return

        for item, count in Counter(value).items():
            if count > 1:
                raise ValidationError(f"Duplicate value: {item!r}")


def ArrayFilterFactory(_parameter_name, _title=None):  # noqa: N802
    class ArrayFieldListFilter(SimpleListFilter):
        title = _title or _parameter_name
        parameter_name = _parameter_name

        def lookups(self, request, model_admin):
            array_values = model_admin.model.objects.values_list(
                self.parameter_name, flat=True
            ).distinct()

            return sorted(
                {
                    (value, value)
                    for array_value in array_values
                    for value in array_value
                }
            )

        def queryset(self, request, queryset):
            lookup_value = self.value()
            if lookup_value:
                queryset = queryset.filter(
                    **{f"{self.parameter_name}__contains": [lookup_value]}
                )
            return queryset

    return ArrayFieldListFilter


class ArrayLength(Func):
    function = "array_length"

    def __init__(self, array_field, dimension=1, **kwargs):
        if "output_field" not in kwargs:
            kwargs["output_field"] = models.IntegerField()
        super().__init__(array_field, dimension, **kwargs)
