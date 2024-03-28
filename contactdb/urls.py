from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, re_path
from django.urls import path
from django.views.decorators.cache import never_cache
from two_factor.urls import urlpatterns as tf_urls
from django.contrib.auth.decorators import login_required
from ckeditor_uploader import views

from django.contrib.auth import views as auth_views
from common.protected_media import protected_serve

urlpatterns = [
    re_path(
        r"^protected_media/(?P<path>.*)$",
        protected_serve,
        kwargs={"document_root": settings.PROTECTED_MEDIA_ROOT},
    ),
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    path("django_task/", include("django_task.urls", namespace="django_task")),
    path(r"ckeditor/upload/", login_required(views.upload), name="ckeditor_upload"),
    path(
        r"ckeditor/browse/",
        never_cache(login_required(views.browse)),
        name="ckeditor_browse",
    ),
    path("", include(tf_urls)),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("", admin.site.urls),
]


if settings.DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns.insert(0, path("__debug__/", include(debug_toolbar.urls)))
