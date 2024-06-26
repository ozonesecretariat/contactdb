from functools import update_wrapper

from constance import config
from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.shortcuts import redirect
from django.urls import reverse


def should_redirect_setup_2fa(user):
    return config.REQUIRE_2FA and not user.two_factor_enabled


class ContactDBAdminSite(AdminSite):
    site_title = "Ozone Contact DB"
    site_header = "Ozone Contact DB"
    index_title = "Ozone Contact DB"

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label=app_label)
        for app_dict in app_list:
            for model_dict in app_dict["models"]:
                model_admin = self._registry[model_dict["model"]]
                if getattr(model_admin, "show_index_page_count", False):
                    model_dict["name"] += f" ({model_admin.get_index_page_count()})"

        return app_list

    def admin_view(self, view, cacheable=False):
        view = super().admin_view(view, cacheable)

        def inner(request, *args, **kwargs):
            if self.has_permission(request) and should_redirect_setup_2fa(request.user):
                return redirect(reverse("two_factor:setup"))
            return view(request, *args, **kwargs)

        return update_wrapper(inner, view)


class ContactDBAdminConfig(AdminConfig):
    default_site = "contactdb.site.ContactDBAdminSite"
