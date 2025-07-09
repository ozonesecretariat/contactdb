from io import BytesIO

from django.conf import settings
from django.template.loader import get_template
from weasyprint import HTML


def print_pdf(template, context=None, request=None):
    template = get_template(template)
    html = template.render(context=context, request=request)

    pdf = HTML(
        string=html,
        base_url=settings.PROTOCOL + settings.MAIN_BACKEND_HOST,
    ).write_pdf()
    fp = BytesIO()
    fp.write(pdf)
    fp.seek(0)

    return fp
