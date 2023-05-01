from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include
from django.urls import path
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from two_factor.urls import urlpatterns as tf_urls

from accounts.views import RedirectLoginView
from core.views import HomepageView, RecordDetailView

urlpatterns = [
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    path("django_task/", include("django_task.urls", namespace="django_task")),
    path(
        "admin/password_reset/",
        auth_views.PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path(
        "admin/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "admin/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "admin/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("admin/", admin.site.urls),
    path("accounts/profile/", RedirectView.as_view(pattern_name="two_factor:profile")),
    path("account/login/", RedirectLoginView.as_view(), name="login"),
    path("", include(tf_urls)),
    path("account/logout/", LogoutView.as_view(), name="logout"),
    path("", HomepageView.as_view(), name="home"),
    path("contacts/<pk>", RecordDetailView.as_view(), name="contact-detail"),
]

if settings.DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
