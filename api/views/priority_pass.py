from rest_framework import viewsets

from api.serializers.priority_pass import PriorityPassSerializer
from events.models import PriorityPass


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
