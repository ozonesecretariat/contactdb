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
from core.views import (
    HomepageView,
    RecordDetailView,
    RecordDeleteView,
    RecordUpdateView,
    ContactListView,
    RegistrationStatusListView,
    GroupListView,
    GroupDetailView,
    GroupMembersView,
    GroupDeleteView,
    GroupUpdateView, AddGroupMemberView, SearchContactView,
)

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
    path("contacts/", ContactListView.as_view(), name="contact-list"),
    path("contacts/<pk>", RecordDetailView.as_view(), name="contact-detail"),
    path("contacts/<pk>/delete", RecordDeleteView.as_view(), name="contact-delete"),
    path("contacts/<pk>/update", RecordUpdateView.as_view(), name="contact-update"),
    path(
        "registration-statuses/",
        RegistrationStatusListView.as_view(),
        name="registration-status-list",
    ),
    path("groups/", GroupListView.as_view(), name="group-list"),
    path("groups/<pk>", GroupDetailView.as_view(), name="group-detail"),
    path("groups/members/", GroupMembersView.as_view(), name="group-members"),
    path("groups/<pk>/delete", GroupDeleteView.as_view(), name="group-delete"),
    path("groups/<pk>/update", GroupUpdateView.as_view(), name="group-update"),
    path("groups/<pk>/add-member", AddGroupMemberView.as_view(), name="group-add-member"),
    path("groups/search-contact/", SearchContactView.as_view(), name="search-contact"),
]

if settings.DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
