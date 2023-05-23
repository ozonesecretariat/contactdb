import django_filters
from django.db.models import Q
from core.models import Record, Organization, RegistrationStatus, Group
from django import forms

MAILING_LIST = (
    (True, "Yes"),
    (False, "No"),
)


class RecordFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        method="name_search", widget=forms.TextInput(attrs={"class": "form-control"})
    )
    department = django_filters.CharFilter(
        lookup_expr="icontains", widget=forms.TextInput(attrs={"class": "form-control"})
    )
    designation = django_filters.CharFilter(
        lookup_expr="icontains", widget=forms.TextInput(attrs={"class": "form-control"})
    )
    is_in_mailing_list = django_filters.ChoiceFilter(
        choices=MAILING_LIST, widget=forms.Select(attrs={"class": "form-select"})
    )
    is_use_organization_address = django_filters.ChoiceFilter(
        choices=MAILING_LIST, widget=forms.Select(attrs={"class": "form-select"})
    )
    organization = django_filters.ChoiceFilter(
        choices=Organization.objects.all().values_list("id", "name"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    emails = django_filters.CharFilter(
        method="email_search", widget=forms.TextInput(attrs={"class": "form-control"})
    )
    phones_faxes = django_filters.CharFilter(
        method="phone_faxes_search",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Record
        fields = [
            "name",
            "department",
            "designation",
            "is_in_mailing_list",
            "is_use_organization_address",
            "organization",
            "emails",
            "phones_faxes",
        ]

    def name_search(self, queryset, name, value):
        for term in value.split():
            queryset = queryset.filter(
                Q(first_name__icontains=term) | Q(last_name__icontains=term)
            )
        return queryset

    def email_search(self, queryset, name, value):
        return queryset.filter(
            Q(emails__icontains=value) | Q(email_ccs__icontains=value)
        )

    def phone_faxes_search(self, queryset, name, value):
        return queryset.filter(
            Q(phones__icontains=value)
            | Q(mobiles__icontains=value)
            | Q(faxes__icontains=value)
        )


class RegistrationStatusFilter(django_filters.FilterSet):
    class Meta:
        model = RegistrationStatus
        fields = ["contact", "role", "status", "is_funded", "date"]


class GroupFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        method="name_search", widget=forms.TextInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = Record
        fields = ["name"]

    def name_search(self, queryset, name, value):
        for term in value.split():
            queryset = queryset.filter(Q(name__icontains=term))
        return queryset


class GroupMembersFilter(django_filters.FilterSet):
    class Meta:
        model = Record
        fields = ["group"]


class SearchContactFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        method="name_search", widget=forms.TextInput(attrs={"class": "form-control"})
    )

    group = django_filters.ChoiceFilter(
        method="not_in_group",
        choices=Group.objects.all().values_list("id", "name"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Record
        fields = ["name", "group"]

    def name_search(self, queryset, name, value):
        for term in value.split():
            queryset = queryset.filter(
                Q(first_name__icontains=term) | Q(last_name__icontains=term)
            )
        return queryset

    def not_in_group(self, queryset, name, value):
        return queryset.filter(~Q(group=value))
