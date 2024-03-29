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
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView
from two_factor.urls import urlpatterns as tf_urls
from django.contrib.auth.decorators import login_required
from ckeditor_uploader import views
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
    EmailPage,
    SyncKronosView,
    RunKronosEventsImport,
    LoadKronosEventsView,
    RunKronosParticipantsImport,
    LoadKronosParticipantsView,
    ResolveConflictsView,
    ResolveAllConflictsFormView,
    ConflictsResolvedView,
    ResolveConflictsFormView,
    AllConflictsResolvedView,
    ConflictsResolvingView,
    NoConflictsView,
    MergeContactsSecondStepView,
    MergeContactsView,
    MergeContactsFirstStepView,
    MergeSuccessView,
    RecordCreateView,
    EmailListView,
    ContactEmailsHistory,
    GroupEmailsHistory,
    EmailDetailView,
    EmailTemplateCreateView,
    EmailTemplateCreateSuccessView,
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
    path(
        "contacts/<pk>/emails-history/",
        ContactEmailsHistory.as_view(),
        name="contact-emails-history",
    ),
    path("contacts/<pk>/delete/", RecordDeleteView.as_view(), name="contact-delete"),
    path("contacts/<pk>/update/", RecordUpdateView.as_view(), name="contact-update"),
    path("contacts/create/", RecordCreateView.as_view(), name="contact-create"),
    path(
        "registration-statuses/",
        RegistrationStatusListView.as_view(),
        name="registration-status-list",
    ),
    path("groups/", GroupListView.as_view(), name="group-list"),
    path("groups/create/", GroupCreateView.as_view(), name="group-create"),
    path("groups/<pk>", GroupDetailView.as_view(), name="group-detail"),
    path(
        "groups/<pk>/emails-history",
        GroupEmailsHistory.as_view(),
        name="group-emails-history",
    ),
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
    path("emails/", EmailPage.as_view(), name="emails-page"),
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
        name="conflict-resolution",
    ),
    path(
        "sync-kronos/conflict-resolution/resolve-all",
        ResolveAllConflictsFormView.as_view(),
        name="resolve-all-conflicts",
    ),
    path(
        "sync-kronos/conflict-resolution/resolve-conflict",
        ResolveConflictsFormView.as_view(),
        name="resolve-conflict",
    ),
    path(
        "sync-kronos/conflict-resolution/conflicts-resolved",
        ConflictsResolvedView.as_view(),
        name="conflict-resolved",
    ),
    path(
        "sync-kronos/conflict-resolution/all-conflicts-resolved",
        AllConflictsResolvedView.as_view(),
        name="all-conflicts-resolved",
    ),
    path(
        "sync-kronos/conflict-resolution/conflicts-resolving",
        ConflictsResolvingView.as_view(),
        name="conflicts-resolving",
    ),
    path(
        "sync-kronos/conflict-resolution/no-conflicts",
        NoConflictsView.as_view(),
        name="no-conflicts",
    ),
    path(
        "contacts/merge-contacts/",
        MergeContactsView.as_view(),
        name="merge-contacts",
    ),
    path(
        "contacts/merge-contacts/first-step/",
        MergeContactsFirstStepView.as_view(),
        name="merge-first-step",
    ),
    path(
        "contacts/merge-contacts/second-step/",
        MergeContactsSecondStepView.as_view(),
        name="merge-second-step",
    ),
    path(
        "contacts/merge-contacts/success/",
        MergeSuccessView.as_view(),
        name="merge-success",
    ),
    path("emails/history/", EmailListView.as_view(), name="emails-history"),
    path("emails/<pk>", EmailDetailView.as_view(), name="email-detail"),
    path(
        "email_templates/create/",
        EmailTemplateCreateView.as_view(),
        name="email-template-create",
    ),
    path(
        "email_templates/create/success/",
        EmailTemplateCreateSuccessView.as_view(),
        name="email-template-create-success",
    ),
    path(r"ckeditor/upload/", login_required(views.upload), name="ckeditor_upload"),
    path(
        r"ckeditor/browse/",
        never_cache(login_required(views.browse)),
        name="ckeditor_browse",
    ),
]

if settings.DEBUG:
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
