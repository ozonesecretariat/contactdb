from rest_framework.viewsets import ReadOnlyModelViewSet
from api.serializers.event import EventSerializer
from events.models import Event


class EventViewSet(ReadOnlyModelViewSet):
    queryset = Event.objects.all().prefetch_related("venue_country")
    serializer_class = EventSerializer
    lookup_field = "code"
