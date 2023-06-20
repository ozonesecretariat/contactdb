from django import template
from django import forms
from django.contrib.postgres.fields import ArrayField
from django.template.loader import render_to_string

register = template.Library()


@register.filter(name="add_classes")
def add_classes(value, arg):
    default_classes = value.field.widget.attrs.get("class", "")
    classes = []
    args = arg.split(" ")
    for a in args:
        classes.append(a)
    classes_string = default_classes + " ".join(classes)
    return value.as_widget(attrs={"class": classes_string, "placeholder": ""})


@register.filter(name="get_fields")
def get_fields(obj):
    excluded_fields = ["record", "id", "created_at", "updated_at"]
    return [
        field for field in obj._meta.get_fields() if field.name not in excluded_fields
    ]


@register.simple_tag
def conflict_field(obj, compare_obj, field_name, label):
    field = getattr(obj, field_name)
    compare_field = getattr(compare_obj, field_name)
    context = {"field_name": label, "field": field, "compare_field": compare_field}

    if isinstance(field, list):
        context["is_list"] = True

    return render_to_string("conflict_field.html", context)
