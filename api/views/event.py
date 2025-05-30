from functools import lru_cache

from django.utils import timezone
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.serializers.contact import ContactSerializer
from api.serializers.event import (
    EventSerializer,
    RegistrationSerializer,
)
from core.models import Contact
from events.models import Event, EventInvitation, Registration, RegistrationStatus


@lru_cache(maxsize=1)
def get_nomination_status_id():
    return RegistrationStatus.objects.get(name="Nominated").id


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

    def get_invitation(self):
        token = self.kwargs.get("token")
        return EventInvitation.objects.get(token=token)

    def get_queryset(self):
        # Get the invitation using the token from the URL
        invitation = self.get_invitation()
        # TODO: this assumes mutual exclusion between event and event_group
        if invitation.event:
            return [invitation.event]
        return invitation.event_group.events.all()

    @action(detail=False, methods=["get"])
    def available_contacts(self, request):
        """List contacts that can be nominated from this organization."""
        invitation = self.get_invitation()
        contacts = Contact.objects.filter(organization=invitation.organization)
        return Response(ContactSerializer(contacts, many=True).data)

    @action(detail=True, methods=["post"])
    def nominate_contacts(self, request):
        # Get the invitation using the token from the URL
        invitation = self.get_invitation()
        contacts_data = request.data.get("contacts", [])

        # Validate all contacts belong to organization
        for contact_id in contacts_data:
            if not Contact.objects.filter(
                id=contact_id, organization=invitation.organization
            ).exists():
                raise PermissionDenied(
                    f"Contact {contact_id} does not belong to {invitation.organization}"
                )

        registrations = []
        for contact_data in contacts_data:
            registration = Registration.objects.create(
                event=self.get_object(),
                organization=invitation.organization,
                contact=contact_data,
                status_id=get_nomination_status_id(),
                date=timezone.now().date(),
            )
            registrations.append(registration)

        return Response(RegistrationSerializer(registrations, many=True).data)
