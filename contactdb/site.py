from functools import update_wrapper

from constance import config
from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


def should_redirect_setup_2fa(user):
    return config.REQUIRE_2FA and not user.two_factor_enabled


def frontend_path(path: str, request=None):
    path = settings.PROTOCOL + settings.MAIN_FRONTEND_HOST + "/" + path.lstrip("/")
    if request and REDIRECT_FIELD_NAME in request.GET:
        next = request.build_absolute_uri(request.GET[REDIRECT_FIELD_NAME])
        path += f"?{REDIRECT_FIELD_NAME}={next}"
    return path


class ContactDBAdminSite(AdminSite):
    site_title = "Ozone Contact DB"
    site_header = "Ozone Contact DB"
    index_title = "Ozone Contact DB"
    site_url = settings.PROTOCOL + settings.MAIN_FRONTEND_HOST

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
                return redirect(frontend_path("/account/security"))
            return view(request, *args, **kwargs)

        return update_wrapper(inner, view)

    @method_decorator(never_cache)
    @login_not_required
    def login(self, request, extra_context=None):
        return redirect(frontend_path("/auth/login", request=request))

    def password_change(self, request, extra_context=None):
        return redirect(frontend_path("/account/password"))


class ContactDBAdminConfig(AdminConfig):
    default_site = "contactdb.site.ContactDBAdminSite"
