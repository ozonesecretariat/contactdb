from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework import routers

import api.views.user
from api.views.contact import ContactViewSet
from api.views.dsa import DSAViewSet
from api.views.event import EventViewSet
from api.views.misc import AppSettingsView
from api.views.nomination import EventNominationViewSet
from api.views.priority_pass import PriorityPassViewSet
from api.views.registration import RegistrationTagViewSet, RegistrationViewSet

router = routers.SimpleRouter()
router.register("dsa", DSAViewSet)
router.register("events", EventViewSet)
router.register("contacts", ContactViewSet)
router.register("priority-passes", PriorityPassViewSet)
router.register("registrations", RegistrationViewSet)
router.register("registration-tags", RegistrationTagViewSet)
router.register(
    "events-nominations", EventNominationViewSet, basename="events-nominations"
)

urlpatterns = [
    # API DOCS
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path(
        "schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("auth/login/", api.views.user.OTPLoginView.as_view()),
    path("auth/", include("dj_rest_auth.urls")),
    # Two-factor auth setup
    path(
        r"account/two_factor/setup/",
        api.views.user.TwoFactorSetupView.as_view(),
        name="account-two-factor-setup",
    ),
    path(
        r"account/two_factor/setup/qrcode/",
        api.views.user.TwoFactorQRGeneratorView.as_view(),
        name="account-two-factor-qr",
    ),
    path(
        "account/two_factor/backup/tokens/",
        api.views.user.TwoFactorBackupTokensView.as_view(),
        name="account-two-factor-backup-tokens",
    ),
    path(
        "account/two_factor/disable/",
        api.views.user.TwoFactorDisable.as_view(),
        name="account-two-factor-disable",
    ),
    path(
        "app-settings/",
        AppSettingsView.as_view(),
        name="app-settings",
    ),
] + router.urls
