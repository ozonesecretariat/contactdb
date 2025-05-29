from functools import lru_cache
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.serializers.event import EventSerializer, RegistrationSerializer
from events.models import Event, EventInvitation, Registration, RegistrationStatus


@lru_cache(maxsize=1)
def get_nomination_status_id():
    return RegistrationStatus.objects.get(name='nominated').id


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


class EventNominationViewSet(ModelViewSet):
    permission_classes = (AllowAny,)

    def get_queryset(self):
        # Filter by token from URL
        token = self.kwargs.get("token")
        invitation = EventInvitation.objects.get(token=token)
        # TODO: this assumes mutual exclusion between event and event_group
        if invitation.event:
            return [invitation.event]
        return invitation.event_group.events.all()

    @action(detail=True, methods=["post"])
    def nominate_contacts(self, request):
        token = self.kwargs.get("token")
        invitation = EventInvitation.objects.get(token=token)
        contacts_data = request.data.get("contacts", [])

        registrations = []
        for contact_data in contacts_data:
            registration = Registration.objects.create(
                event=self.get_object(),
                organization=invitation.organization,
                contact=contact_data,
                status_id=get_nomination_status_id(),
            )
            registrations.append(registration)

        return Response(RegistrationSerializer(registrations, many=True).data)
