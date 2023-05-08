from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from core.models import Record
from core.tables import RecordTable
from core.filters import RecordFilter


class HomepageView(LoginRequiredMixin, TemplateView):
    template_name = "home_page.html"


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
