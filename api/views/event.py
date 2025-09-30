import django_filters
from django.contrib.auth.decorators import permission_required
from django.db.models import Case, Count, F, Value, When
from django.utils import timezone
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.serializers.event import (
    EventSerializer,
)
from common.filters import CamelCaseOrderingFilter
from core.models import Contact, OrganizationType, Region, Subregion
from events.models import AnnotatedRegistration, Event, Registration, RegistrationRole


class EventFilterSet(FilterSet):
    is_current = django_filters.BooleanFilter(method='filter_is_current')

    class Meta:
        model = Event
        fields = ['is_current']

    def filter_is_current(self, queryset, name, value):
        today = timezone.now().date()

        if value:
            return queryset.filter(end_date__gte=today)
        return queryset.filter(end_date__lt=today)


class EventViewSet(ReadOnlyModelViewSet):
    queryset = Event.objects.all().select_related("venue_country")
    serializer_class = EventSerializer
    lookup_field = "code"
    filter_backends = [filters.SearchFilter, CamelCaseOrderingFilter, DjangoFilterBackend]
    filterset_class = EventFilterSet
    search_fields = [
        "code",
        "title",
        "venue_city",
        "venue_country__name",
        "venue_country__official_name",
    ]
    ordering_fields = ["code", "title", "start_date", "end_date"]
    ordering = ["code"]

    @method_decorator(permission_required("events.view_event", raise_exception=True))
    @action(detail=True, methods=["get"])
    def statistics(self, *args, **kwargs):
        event = self.get_object()

        regs = (
            AnnotatedRegistration.objects.filter(registration__event=event)
            .exclude(usable_organization__organization_type__hide_in_statistics=True)
            .annotate(
                organization_type=Case(
                    When(
                        usable_organization__organization_type__statistics_title="",
                        then=F("usable_organization__organization_type__title"),
                    ),
                    default=F(
                        "usable_organization__organization_type__statistics_title"
                    ),
                ),
                region=F("usable_organization__government__region__name"),
                subregion=F("usable_organization__government__subregion__name"),
                gender=Case(
                    When(registration__contact__gender="", then=Value("N/A")),
                    default=F("registration__contact__gender"),
                ),
                status=F("registration__status"),
                role=F("registration__role__name"),
            )
            .values(
                "organization_type",
                "region",
                "subregion",
                "gender",
                "status",
                "role",
            )
            .annotate(count=Count(1))
        )

        org_type_query = OrganizationType.objects.exclude(
            hide_in_statistics=True
        ).order_by("sort_order")
        org_types = []
        for org_type in org_type_query:
            if org_type.statistics_display_name not in org_types:
                org_types.append(org_type.statistics_display_name)

        return Response(
            {
                "registrations": regs,
                "schema": {
                    "role": RegistrationRole.objects.values_list(
                        "name", flat=True
                    ).order_by("sort_order"),
                    "region": Region.objects.values_list("name", flat=True).order_by(
                        "sort_order"
                    ),
                    "subregion": Subregion.objects.values_list(
                        "name", flat=True
                    ).order_by("sort_order"),
                    "organization_type": org_types,
                    "status": [i[0] for i in Registration.Status.choices],
                    "gender": [i[0] for i in Contact.GenderChoices.choices] + ["N/A"],
                },
            }
        )
