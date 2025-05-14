from rest_framework import filters
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.serializers.event import EventSerializer
from events.models import Event


class EventViewSet(ReadOnlyModelViewSet):
    queryset = Event.objects.all().prefetch_related("venue_country")
    serializer_class = EventSerializer
    lookup_field = "code"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "code",
        "title",
        "venue_city",
        "venue_country__name",
        "venue_country__official_name",
    ]
    ordering_fields = ["code", "title", "start_date", "end_date"]
    ordering = ["code"]
