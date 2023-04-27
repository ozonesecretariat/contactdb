from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView


# Create your views here.


class HomepageView(LoginRequiredMixin, TemplateView):
    template_name = "home_page.html"
