from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework import routers

import api.views.user
from api.views.event import EventNominationViewSet, EventViewSet
from api.views.misc import AppSettingsView

router = routers.SimpleRouter()
router.register("events", EventViewSet)
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
