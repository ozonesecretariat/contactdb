import json
from urllib.parse import parse_qs

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import Http404
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import (
    TemplateView,
    DetailView,
    DeleteView,
    UpdateView,
    ListView,
)
from django.views.generic.edit import FormMixin, FormView

from core.forms import RecordUpdateForm, GroupUpdateForm, AddGroupMemberForm, AddMultipleGroupMembersForm

from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from core.models import Record, RegistrationStatus, Group
from core.tables import RecordTable, GroupTable, GroupMemberTable
from core.filters import (
    RecordFilter,
    RegistrationStatusFilter,
    GroupFilter,
    GroupMembersFilter, SearchContactFilter,
)


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

    def get(self, request, *args, **kwargs):
        print(self.get_filterset(self.get_filterset_class()).qs)

        return super().get(request, *args, **kwargs)


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


class GroupListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    table_class = GroupTable
    queryset = Group.objects.all()
    filterset_class = GroupFilter
    paginate_by = 1

    def get_template_names(self):
        if self.request.htmx:
            template_name = "core/group_list_partial.html"
        else:
            template_name = "core/group_list.html"

        return template_name


class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group


class GroupMembersView(LoginRequiredMixin, SingleTableMixin, FilterView):
    table_class = GroupMemberTable
    queryset = Record.objects.all()
    filterset_class = GroupMembersFilter
    paginate_by = 20

    def get_template_names(self):
        if self.request.htmx:
            template_name = "core/group_members_partial.html"
        else:
            template_name = "404.html"

        return template_name

    def get(self, request, *args, **kwargs):
        if self.request.htmx:
            return super().get(request, *args, **kwargs)
        else:
            raise Http404


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Group

    def get_success_url(self):
        return reverse("group-list")

    def has_permission(self):
        return self.request.user.can_edit


class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Group
    form_class = GroupUpdateForm

    def has_permission(self):
        return self.request.user.can_edit

    def get_success_url(self):
        return reverse("group-detail", kwargs={"pk": self.object.pk})


class SearchContactView(LoginRequiredMixin, FilterView, ListView):
    model = Record
    filterset_class = SearchContactFilter
    context_object_name = "contacts"
    ordering = ["first_name", "last_name"]

    def get_template_names(self):
        if self.request.htmx:
            template_name = "core/select_member_list.html"
        else:
            template_name = ""

        return template_name

    def get(self, request, *args, **kwargs):
        if self.request.htmx:
            return super().get(request, *args, **kwargs)
        else:
            raise Http404


class AddGroupMemberView(LoginRequiredMixin, PermissionRequiredMixin, FormMixin, DetailView):
    template_name = "core/add_group_member.html"
    form_class = AddGroupMemberForm
    model = Group

    def has_permission(self):
        return self.request.user.can_edit

    def get_success_url(self):
        return reverse("group-detail", kwargs={"pk": self.object.pk})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.object = self.get_object()

        if form.is_valid():
            self.new_member = Record.objects.filter(pk=form.cleaned_data["new_member_id"]).first()
            if self.new_member is not None:
                return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        self.object.contacts.add(self.new_member)
        self.object.save()
        return super().form_valid(form)


class AddMultipleGroupMembersView(LoginRequiredMixin, PermissionRequiredMixin, FilterView, FormMixin):
    form_class = AddMultipleGroupMembersForm
    model = Record
    template_name = 'core/add_multiple_group_members.html'
    filterset_class = RecordFilter

    def has_permission(self):
        return self.request.user.can_edit

    def get_success_url(self):
        return reverse("group-list")

    def get_template_names(self):
        if self.request.htmx:
            template_name = "core/add_multiple_group_members_partial.html"
        else:
            template_name = "core/add_multiple_group_members.html"

        return template_name

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_filterset(self.filterset_class).qs
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        members = Record.objects.filter(id__in=form.cleaned_data["members"])
        groups = Group.objects.filter(id__in=form.cleaned_data["groups"])
        for group in groups:
            group.contacts.add(*members.all())
        return super().form_valid(form)

    def form_invalid(self, form):
        f = self.get_filterset(self.filterset_class)
        previously_selected_members = []
        member_ids = form.cleaned_data.get("members")
        if member_ids and len(member_ids) > 0:
            previously_selected_members = Record.objects.filter(id__in=member_ids)
        return self.render_to_response(self.get_context_data(form=form, filter=f, previously_selected_members=previously_selected_members))
