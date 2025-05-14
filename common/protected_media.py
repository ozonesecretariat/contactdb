import django.apps
from django.core.files.storage import storages
from django.db import models
from django.http import HttpResponseForbidden
from django.views.static import serve

from common.permissions import has_model_permission


def has_folder_permission(request, path):
    folder = path.split("/", 1)[0]

    for model in django.apps.apps.get_models():
        for field in model._meta.get_fields():
            # XXX NOTE THAT THIS ASSUMES EACH MODEL UPLOADS TO A DIFFERENT FOLDER.
            # XXX IF MULTIPLE MODELS UPLOAD TO THE SAME FOLDER THIS WILL RESULT IN
            # XXX PRIVILEGE ESCALATION.
            # Find what model uploads to this folder and check if the user has
            # view permission for it.
            if (
                isinstance(field, models.FileField)
                and field.storage == storages["protected"]
                and field.upload_to.strip("/") == folder
                and has_model_permission(request, model, "view")
            ):
                return True
    return False


def protected_serve(request, path, document_root=None, show_indexes=False):
    if (
        request.user
        and request.user.is_authenticated
        and has_folder_permission(request, path)
    ):
        return serve(
            request, path, document_root=document_root, show_indexes=show_indexes
        )

    return HttpResponseForbidden()
