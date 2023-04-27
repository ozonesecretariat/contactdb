import logging

from django.shortcuts import redirect
from django.urls import reverse
from two_factor.views import LoginView


class RedirectLoginView(LoginView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logging.warning("User is already authenticated")
            return redirect(reverse("home"))
        return super().get(request, *args, **kwargs)
