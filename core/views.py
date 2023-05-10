from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import Http404
from django.urls import reverse
from django.views.generic import (
    TemplateView,
    DetailView,
    DeleteView,
    UpdateView,
    ListView,
)

from core.forms import RecordUpdateForm

from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from core.models import Record, RegistrationStatus
from core.tables import RecordTable
from core.filters import RecordFilter, RegistrationStatusFilter


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

    def get_success_url(self):
        return reverse("contact-list")

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


class RegistrationStatusListView(LoginRequiredMixin, FilterView, ListView):
    model = RegistrationStatus
    context_object_name = "statuses"
    filterset_class = RegistrationStatusFilter
    paginate_by = 10
    ordering = ["-date"]

    def get_template_names(self):
        if self.request.htmx:
            template_name = "core/registration_status_list_partial.html"
        else:
            template_name = "core/registration_status_list.html"

        return template_name

    def get(self, request, *args, **kwargs):
        if self.request.htmx:
            return super().get(request, *args, **kwargs)
        else:
            raise Http404

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        page = self.request.GET.get("page", 1)
        paginator = context["paginator"]
        context["pagination_range"] = paginator.get_elided_page_range(
            number=page, on_each_side=1, on_ends=1
        )
        return context
