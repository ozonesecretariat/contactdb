from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
    PasswordChangeView,
    PasswordChangeDoneView,
)
from django.urls import include
from django.urls import path
from django.views.generic import RedirectView
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
    GroupUpdateView,
    AddGroupMemberView,
    SearchContactView,
    AddMultipleGroupMembersView,
    GroupCreateView,
    ImportData,
    ExportExcel,
    ExportDoc,
    SyncKronosView,
    RunKronosEventsImport,
    LoadKronosEventsView,
    RunKronosParticipantsImport,
    LoadKronosParticipantsView, ResolveConflictsView,
)

urlpatterns = [
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    path("django_task/", include("django_task.urls", namespace="django_task")),
    path(
        "account/password-change/", PasswordChangeView.as_view(), name="password_change"
    ),
    path(
        "account/password-change/done/",
        PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path("account/password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "account/password-reset/done/",
        PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "account/reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "account/reset/done/",
        PasswordResetCompleteView.as_view(),
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
    path("groups/create/", GroupCreateView.as_view(), name="group-create"),
    path("groups/<pk>", GroupDetailView.as_view(), name="group-detail"),
    path("groups/members/", GroupMembersView.as_view(), name="group-members"),
    path("groups/<pk>/delete", GroupDeleteView.as_view(), name="group-delete"),
    path("groups/<pk>/update", GroupUpdateView.as_view(), name="group-update"),
    path(
        "groups/<pk>/add-member", AddGroupMemberView.as_view(), name="group-add-member"
    ),
    path("groups/search-contact/", SearchContactView.as_view(), name="search-contact"),
    path(
        "groups/add-members/",
        AddMultipleGroupMembersView.as_view(),
        name="groups-add-multiple-members",
    ),
    path("import-contacts/", ImportData.as_view(), name="import-contacts"),
    path("export-xlsx/", ExportExcel.as_view(), name="export-excel"),
    path("export-docx/", ExportDoc.as_view(), name="export-docx"),
    path("sync-kronos/", SyncKronosView.as_view(), name="sync-kronos"),
    path(
        "kronos-events-import/",
        RunKronosEventsImport.as_view(),
        name="kronos-events-import",
    ),
    path(
        "kronos-events-history/",
        LoadKronosEventsView.as_view(),
        name="kronos-events-import-history",
    ),
    path(
        "kronos-participants-import/",
        RunKronosParticipantsImport.as_view(),
        name="kronos-participants-import",
    ),
    path(
        "kronos-participants-history/",
        LoadKronosParticipantsView.as_view(),
        name="kronos-participants-import-history",
    ),
    path(
        "sync-kronos/conflict-resolution/",
        ResolveConflictsView.as_view(),
        name="conflict-resolution"
    )
]

if settings.DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
