import two_factor
from django_otp import devices_for_user
from django_otp.plugins.otp_static.models import StaticToken
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from two_factor.views import QRGeneratorView, SetupView, LoginView


class OTPLoginView(LoginView, APIView):
    permission_classes = (AllowAny,)
    parser_classes = (FormParser, MultiPartParser)

    def post(self, *args, **kwargs):
        self.prefix = ""
        return super().post(*args, **kwargs)

    def render(self, form=None, **kwargs):
        super().render(form, **kwargs)
        form = form or self.get_form()
        return Response(
            {
                "logged_in": False,
                "success": not form.errors,
                "details": form.errors,
            },
            400 if form.errors else 200,
        )

    def done(self, form_list, **kwargs):
        super().done(form_list, **kwargs)
        return Response(
            {
                "logged_in": True,
            }
        )


class TwoFactorQRGeneratorView(QRGeneratorView):
    pass


class TwoFactorSetupView(SetupView, APIView):
    success_url = "account-two-factor-setup"
    qrcode_url = "account-two-factor-qr"
    parser_classes = (FormParser, MultiPartParser)

    def render(self, form=None, **kwargs):
        super().render(form, **kwargs)
        form = form or self.get_form()
        return Response(
            {
                "success": not form.errors,
                "details": form.errors,
            },
            400 if form.errors else 200,
        )

    def done(self, form_list, **kwargs):
        super().done(form_list, **kwargs)
        return Response(
            {
                "success": True,
            }
        )


class TwoFactorBackupTokensView(APIView):
    number_of_tokens = 10
    permission_classes = (IsAuthenticated,)

    def get_device(self):
        return self.request.user.staticdevice_set.get_or_create(name="backup")[0]

    def post(self, request, **kwargs):
        tokens = []
        device = self.get_device()
        device.token_set.all().delete()
        for n in range(self.number_of_tokens):
            token = StaticToken.random_token()
            device.token_set.create(token=token)
            tokens.append(token)
        return Response(
            {
                "success": True,
                "tokens": tokens,
            }
        )


class TwoFactorDisable(APIView):
    def post(self, request, **kwargs):
        for device in devices_for_user(self.request.user):
            device.delete()
        return Response(
            {
                "success": True,
            }
        )
