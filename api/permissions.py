import rest_framework.permissions


class DjangoModelPermissions(rest_framework.permissions.DjangoModelPermissions):
    """Also enforces the view permission, unlike the rest_framework default."""

    perms_map = {
        **rest_framework.permissions.DjangoModelPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
    }
