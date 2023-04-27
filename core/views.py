from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class HomepageView(LoginRequiredMixin, TemplateView):
    template_name = "home_page.html"
