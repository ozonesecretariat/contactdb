from constance import config
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class AppSettingsView(APIView):
    permission_classes = (AllowAny,)

    @method_decorator(ensure_csrf_cookie)
    @method_decorator(never_cache)
    def get(self, *args, **kwargs):
        return Response(
            {
                "environment_name": settings.ENVIRONMENT_NAME,
                "require_2fa": config.REQUIRE_2FA,
            }
        )
