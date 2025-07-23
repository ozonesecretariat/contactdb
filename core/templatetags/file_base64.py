import base64
import mimetypes

from django import template

register = template.Library()


@register.filter
def file_to_base64(file_field):
    if not file_field:
        return ""

    file_content = file_field.read()
    mime_type, _ = mimetypes.guess_type(file_field.name)
    if not mime_type:
        mime_type = "application/octet-stream"

    base64_data = base64.b64encode(file_content).decode("utf-8")
    return f"data:{mime_type};base64,{base64_data}"
