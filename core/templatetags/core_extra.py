from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def admin_docs(context):
    try:
        # Get either the add/change form or the changelist (cl)
        model_admin = (context.get("adminform") or context.get("cl")).model_admin
        return model_admin.__doc__
    except AttributeError:
        return ""
