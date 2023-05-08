from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView, DetailView, DeleteView, UpdateView

from core.forms import RecordUpdateForm
from core.models import Record

from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from core.models import Record
from core.tables import RecordTable
from core.filters import RecordFilter


class HomepageView(LoginRequiredMixin, TemplateView):
    template_name = "core/home_page.html"


class RecordDetailView(LoginRequiredMixin, DetailView):
    model = Record


class RecordUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Record
    form_class = RecordUpdateForm

    def has_permission(self):
        return self.request.user.can_edit

    def get_success_url(self):
        return reverse("contact-detail", kwargs={"pk": self.object.pk})


class RecordDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Record
    success_url = "/"

    def has_permission(self):
        return self.request.user.can_edit


class ContactListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    table_class = RecordTable
    queryset = Record.objects.all()
    filterset_class = RecordFilter
    paginate_by = 30

    def get_template_names(self):
        if self.request.htmx:
            template_name = "records_list_page_partial.html"
        else:
            template_name = "records_list_page.html"

        return template_name
