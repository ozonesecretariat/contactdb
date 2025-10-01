from django.contrib.auth.decorators import permission_required
from django.http import FileResponse
from django.utils.decorators import method_decorator
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.serializers.event import (
    EventSerializer,
)
from common.filters import CamelCaseOrderingFilter
from events.exports.dsa import DSAReport
from events.models import (
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

    @method_decorator(permission_required("events.view_dsa", raise_exception=True))
    @action(detail=True, methods=["get"])
    def export_dsa(self, *args, **kwargs):
        event = self.get_object()
        return FileResponse(DSAReport(event).export_xlsx(), as_attachment=True)
