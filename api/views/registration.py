import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import filters, viewsets

from api.serializers.event import (
    RegistrationDSASerializer,
    RegistrationTagSerializer,
)
from common.filters import CamelCaseOrderingFilter
from events.models import Registration, RegistrationTag


class RegistrationDSAFilter(FilterSet):
    event_code = django_filters.CharFilter(
        field_name="event__code", lookup_expr="iexact"
    )
    paid_dsa = django_filters.BooleanFilter(
        field_name="dsa__paid_dsa", method="filter_paid_dsa"
    )
    priority_pass_code = django_filters.CharFilter(
        field_name="priority_pass__code", lookup_expr="iexact"
    )
    tag = django_filters.CharFilter(field_name="tags__name", lookup_expr="iexact")

    class Meta:
        model = Registration
        fields = (
            "event_code",
            "status",
            "paid_dsa",
            "tag",
        )

    def filter_paid_dsa(self, queryset, name, value):
        if value is True:
            return queryset.filter(**{name: True})
        if value is False:
            # Match both False and None
            return queryset.filter(Q(**{name: False}) | Q(**{f"{name}__isnull": True}))
        return queryset


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = (
        Registration.objects.all()
        .select_related("dsa")
        .prefetch_related(
            "role",
            "tags",
            "event",
            "event__venue_country",
            "organization",
            "organization__government",
            "organization__country",
            "organization__organization_type",
            "contact",
            "contact__country",
            "contact__organization",
            "contact__organization__government",
            "contact__organization__country",
            "contact__organization__organization_type",
        )
        .order_by("contact__last_name", "contact__first_name")
    )
    serializer_class = RegistrationDSASerializer
    filter_backends = (
        filters.SearchFilter,
        CamelCaseOrderingFilter,
        DjangoFilterBackend,
    )
    filterset_class = RegistrationDSAFilter
    search_fields = (
        "contact__title",
        "contact__first_name",
        "contact__last_name",
        "organization__name",
    )


class RegistrationTagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RegistrationTag.objects.all()
    serializer_class = RegistrationTagSerializer
