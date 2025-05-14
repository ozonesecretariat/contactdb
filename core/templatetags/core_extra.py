from django import template

from common.urls import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def admin_docs(context):
    try:
        # Get either the add/change form or the changelist (cl)
        model_admin = (context.get("adminform") or context.get("cl")).model_admin
        return model_admin.__doc__
    except AttributeError:
        return ""


@register.simple_tag(takes_context=True)
def admin_export_url(context):
    opts = context["opts"]
    return reverse(f"admin:{opts.app_label}_{opts.model_name}_export")
