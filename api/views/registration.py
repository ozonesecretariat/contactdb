import django_filters
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.http import FileResponse
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404

from api.serializers.event import (
    RegistrationDSASerializer,
    RegistrationTagSerializer,
)
from common.filters import CamelCaseOrderingFilter, CharInFilter
from events.exports.dsa import DSAFiles, DSAReport
from events.models import Event, Registration, RegistrationTag


class RegistrationTagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RegistrationTag.objects.all()
    serializer_class = RegistrationTagSerializer


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
    status = CharInFilter(lookup_expr="in")

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
        "contact__first_name__unaccent",
        "contact__last_name__unaccent",
        "organization__name__unaccent",
    )

    @method_decorator(permission_required("events.view_dsa", raise_exception=True))
    @action(detail=False, methods=["get"])
    def export_dsa(self, *args, **kwargs):
        event = get_object_or_404(
            Event.objects, code=self.request.GET.get("event_code")
        )
        queryset = self.filter_queryset(self.get_queryset())
        return FileResponse(
            DSAReport(event, queryset=queryset).export_xlsx(), as_attachment=True
        )

    @method_decorator(permission_required("events.view_dsa", raise_exception=True))
    @action(detail=False, methods=["get"])
    def export_dsa_files(self, *args, **kwargs):
        event = get_object_or_404(
            Event.objects, code=self.request.GET.get("event_code")
        )
        queryset = self.filter_queryset(self.get_queryset())
        return FileResponse(
            DSAFiles(event, queryset=queryset).export_zip(), as_attachment=True
        )
