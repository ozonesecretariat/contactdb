from ckeditor_uploader import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView

from common.protected_media import protected_serve

admin_urlpatterns = [
    path("ckeditor/upload/", login_required(views.upload), name="ckeditor_upload"),
    path(
        "ckeditor/browse/",
        never_cache(login_required(views.browse)),
        name="ckeditor_browse",
    ),
    path("", admin.site.urls),
]

urlpatterns = [
    re_path(
        r"^protected_media/(?P<path>.*)$",
        protected_serve,
        kwargs={"document_root": settings.PROTECTED_MEDIA_ROOT},
    ),
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    # XXX Cannot set this under a different prefix as the URL is hardcoded in the
    # XXX django task js scripts.
    path("django_task/", include("django_task.urls", namespace="django_task")),
    path(r"health_check/", include("health_check.urls")),
    path("admin/", include(admin_urlpatterns)),
    path("api/", include("api.urls")),
    path("", RedirectView.as_view(pattern_name="admin:index")),
]


if settings.DJANGO_DEBUG_TOOLBAR:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns.insert(0, path("__debug__/", include(debug_toolbar.urls)))
