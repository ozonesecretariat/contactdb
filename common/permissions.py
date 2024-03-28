from django.contrib.auth import get_permission_codename


def has_model_permission(request, model, permission_code):
    opts = model._meta
    codename = get_permission_codename(permission_code, opts)
    return request.user.has_perm("%s.%s" % (opts.app_label, codename))
