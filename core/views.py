from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView, DetailView, DeleteView, UpdateView

from core.forms import RecordUpdateForm
from core.models import Record


class HomepageView(LoginRequiredMixin, TemplateView):
    template_name = "core/home_page.html"


class RecordDetailView(LoginRequiredMixin, DetailView):
    model = Record


class RecordUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Record
    permission_required = "user.can_edit"
    form_class = RecordUpdateForm

    def get_success_url(self):
        return reverse("contact-detail", kwargs={"pk": self.object.pk})


class RecordDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Record
    permission_required = "user.can_edit"
    success_url = "/"
