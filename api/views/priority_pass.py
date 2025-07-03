from rest_framework import filters, viewsets

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
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
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
