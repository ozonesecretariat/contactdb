from io import BytesIO

from django.template.loader import get_template
from weasyprint import HTML


def print_pdf(template, context=None, request=None):
    template = get_template(template)
    html = template.render(context=context, request=request)

    pdf = HTML(
        string=html,
        base_url=request.build_absolute_uri(),
    ).write_pdf()
    fp = BytesIO()
    fp.write(pdf)
    fp.seek(0)

    return fp
