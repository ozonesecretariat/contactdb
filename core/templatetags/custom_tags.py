from django import template
from django import forms
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import FieldDoesNotExist
from django.template.loader import render_to_string

from core.models import EmailTag

register = template.Library()


@register.filter(name="add_classes")
def add_classes(value, arg):
    default_classes = value.field.widget.attrs.get("class", "")
    classes = []
    args = arg.split(" ")
    for a in args:
        classes.append(a)
    classes_string = default_classes + " " + " ".join(classes)
    return value.as_widget(attrs={"class": classes_string, "placeholder": ""})


@register.filter(name="add_id")
def add_id(value, arg):
    return value.as_widget(attrs={"id": arg})


@register.filter(name="get_fields")
def get_fields(obj):
    excluded_fields = [
        "record",
        "id",
        "created_at",
        "updated_at",
        "registrationstatus",
        "group",
        "recipients",
        "cc",
        "temporarycontact",
    ]
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
    elif isinstance(field, bool):
        context["is_bool"] = True

    return render_to_string("conflict_field.html", context)


@register.simple_tag
def record_detail_field(
    field,
    label,
    is_email=False,
    class_names: str = None,
    small_label=False,
    is_main_contact=False,
):
    context = {
        "field_name": label,
        "field": field,
        "is_email": is_email,
        "is_main_contact": is_main_contact,
        "class_names": class_names,
        "small_label": small_label,
    }

    if isinstance(field, list):
        context["is_list"] = True
    elif isinstance(field, bool):
        context["is_bool"] = True

    return render_to_string("record_detail_field.html", context)


@register.simple_tag
def record_form_field(
    field, class_names: str = None, is_required: bool = False, small_label=False
):
    context = {
        "field": field,
        "is_required": is_required,
        "class_names": class_names,
        "small_label": small_label,
    }

    return render_to_string("record_form_field.html", context)


@register.simple_tag
def merge_contact_field(obj, field_name, label):
    field = getattr(obj, field_name)
    context = {
        "field_name": label,
        "field": field,
    }

    if isinstance(field, list):
        context["is_list"] = True
    elif isinstance(field, bool):
        context["is_bool"] = True

    return render_to_string("merge_contact_field.html", context)


@register.simple_tag
def email_list_field(field, is_group=False):
    context = {
        "field": field,
        "is_group": is_group,
    }

    return render_to_string("email_list_field.html", context)


@register.simple_tag
def email_tags():
    context = {"email_tags": EmailTag.objects.all()}

    return render_to_string("email_tags.html", context)
