from django.contrib.auth.decorators import permission_required
from django.db.models import Count, F
from django.utils.decorators import method_decorator
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.serializers.event import (
    EventSerializer,
)
from common.filters import CamelCaseOrderingFilter
from core.models import Country, OrganizationType, Region, Subregion
from events.models import (
    AnnotatedRegistration,
    Event,
)


class EventViewSet(ReadOnlyModelViewSet):
    queryset = Event.objects.all().select_related("venue_country")
    serializer_class = EventSerializer
    lookup_field = "code"
    filter_backends = [filters.SearchFilter, CamelCaseOrderingFilter]
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
                organization_type=F("usable_organization__organization_type__acronym"),
                government=F("usable_organization__government"),
                region=F("usable_organization__government__region__code"),
                subregion=F("usable_organization__government__subregion__code"),
                gender=F("registration__contact__gender"),
                status=F("registration__status"),
            )
            .values(
                "government",
                "organization_type",
                "region",
                "subregion",
                "gender",
                "status",
            )
            .annotate(count=Count(1))
        )

        return Response(
            {
                "registrations": regs,
                "countries": Country.objects.values(
                    "code", "name", "region", "subregion"
                ).order_by("name"),
                "regions": Region.objects.values("code", "name").order_by("sort_order"),
                "subregions": Subregion.objects.values("code", "name").order_by(
                    "sort_order"
                ),
                "organization_types": OrganizationType.objects.exclude(
                    hide_in_statistics=True
                )
                .values("acronym", "title", "statistics_title")
                .order_by("sort_order"),
            }
        )
