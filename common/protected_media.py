from django.http import Http404, HttpResponseForbidden
from django.views.static import serve
from common.permissions import has_model_permission
from emails.models import EmailAttachment


def protected_serve(request, path, document_root=None, show_indexes=False):
    try:
        assert request.user and request.user.is_authenticated
        folder = path.split("/", 1)[0]
        if folder == "email_files":
            assert has_model_permission(request, EmailAttachment, "view")
        else:
            raise Http404
    except AssertionError:
        return HttpResponseForbidden()

    return serve(request, path, document_root=document_root, show_indexes=show_indexes)
