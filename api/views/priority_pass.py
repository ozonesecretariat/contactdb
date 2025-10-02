import django_filters
from django.utils import timezone
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from api.serializers.priority_pass import PriorityPassSerializer
from common.filters import CamelCaseOrderingFilter
from events.models import PriorityPass


class PriorityPassFilterSet(FilterSet):
    is_current = django_filters.BooleanFilter(method="filter_is_current")

    class Meta:
        model = PriorityPass
        fields = ["is_current"]

    def filter_is_current(self, queryset, name, value):
        today = timezone.now().date()

        if value is True:
            return queryset.filter(registrations__event__end_date__gte=today)
        if value is False:
            return queryset.filter(registrations__event__end_date__lt=today)
        return queryset


class PriorityPassViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "code"
    lookup_url_kwarg = "code"
    serializer_class = PriorityPassSerializer
    queryset = PriorityPass.objects.all().prefetch_related(
        "registrations",
        "registrations__role",
        "registrations__contact",
        "registrations__contact__country",
        "registrations__contact__organization",
        "registrations__contact__organization__country",
        "registrations__contact__organization__government",
        "registrations__organization",
        "registrations__organization__country",
        "registrations__organization__government",
        "registrations__event",
        "registrations__event__venue_country",
    )
    filter_backends = (
        filters.SearchFilter,
        CamelCaseOrderingFilter,
        DjangoFilterBackend,
    )
    search_fields = (
        "registrations__event__code",
        "registrations__event__title__unaccent",
        "registrations__contact__first_name__unaccent",
        "registrations__contact__last_name__unaccent",
        "registrations__contact__emails",
        "registrations__contact__email_ccs",
        "registrations__contact__phones",
        "registrations__contact__organization__name__unaccent",
        "registrations__organization__name__unaccent",
    )
    filterset_class = PriorityPassFilterSet
