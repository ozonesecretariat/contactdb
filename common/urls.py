from urllib.parse import urlencode
from django.urls import reverse as django_reverse


def reverse(
    viewname,
    urlconf=None,
    args=None,
    kwargs=None,
    current_app=None,
    query=None,
):
    """
    Just like django's reverse function but with an optional argument that allows
    encoding a query string as well.
    """
    result = django_reverse(
        viewname, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app
    )
    if query:
        result += "?" + urlencode(query)
    return result
