from functools import lru_cache

from django.db import transaction
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from api.serializers.contact import (
    ContactDetailSerializer,
    ContactSerializer,
    OrganizationSerializer,
)
from api.serializers.event import (
    EventSerializer,
    NominationSerializer,
    RegistrationSerializer,
)
from core.models import Contact, Organization
from events.models import (
    Event,
    EventInvitation,
    Registration,
    RegistrationRole,
    RegistrationStatus,
)


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


class EventNominationViewSet(ViewSet):
    permission_classes = [AllowAny]
    lookup_field = "token"

    def get_invitation(self, token) -> EventInvitation:
        return get_object_or_404(EventInvitation, token=token)

    def get_queryset(self):
        # Get the invitation using the token from the URL
        token = self.kwargs[self.lookup_field]
        invitation = self.get_invitation(token)
        registrations_qs = Registration.objects.select_related(
            "contact", "status", "event"
        )
        if invitation.organization:
            registrations_qs = registrations_qs.filter(
                contact__organization=invitation.organization
            )
        if invitation.country:
            registrations_qs = registrations_qs.filter(
                contact__organization__government=invitation.country,
                contact__organization__organization_type__acronym="GOV",
            )

        # TODO: this assumes mutual exclusion between event and event_group
        if invitation.event:
            return registrations_qs.filter(event=invitation.event)
        return registrations_qs.filter(event__in=invitation.event_group.events.all())

    def get_serializer_class(self):
        """
        Return the appropriate serializer based on action
        """
        serializer_map = {
            "retrieve": RegistrationSerializer,
            "available_contacts": ContactDetailSerializer,
            "create_contact": ContactSerializer,
            "update_contact": ContactSerializer,
            "nominate_contact": NominationSerializer,
            "events": EventSerializer,
            "organizations": OrganizationSerializer,
        }
        return serializer_map[self.action]

    def retrieve(self, request, token):
        registrations = self.get_queryset()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(registrations, many=True)
        return Response(serializer.data)

    def _get_contacts_qs(self, token):
        invitation = self.get_invitation(token)
        query = Contact.objects.all().prefetch_related(
            "organization", "organization__country", "organization__government"
        )

        if invitation.organization:
            query = query.filter(organization=invitation.organization)
        if invitation.country:
            query = query.filter(
                organization__government=invitation.country,
                organization__organization_type__acronym="GOV",
            )
        return query

    @action(detail=True, methods=["get"], url_path="available-contacts")
    def available_contacts(self, request, token):
        """List contacts that can be nominated from this organization."""
        serializer_class = self.get_serializer_class()
        return Response(serializer_class(self._get_contacts_qs(token), many=True).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="nominate-contact/(?P<contact_id>[^/.]+)",
    )
    def nominate_contact(self, request, token, contact_id):
        # Get the invitation using the token from the URL
        contact = get_object_or_404(self._get_contacts_qs(token), id=contact_id)
        available_events = set(self._get_event_qs(token))

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        current_nominations = {
            n.event: n for n in contact.registrations.filter(event__in=available_events)
        }

        with transaction.atomic():
            for nomination in serializer.validated_data:
                event = nomination["event"]
                if event not in available_events:
                    raise ValidationError(
                        {"event": "Contact cannot be nominated in this event"}
                    )

                try:
                    registration = current_nominations.pop(event)
                except KeyError:
                    registration = Registration(event=event, contact=contact)

                registration.role = nomination["role"]
                registration.save()

            # Anything left needs of the current nominations that was not provided
            # needs to be removed.
            for registration in current_nominations.values():
                registration.delete()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="create-contact")
    def create_contact(self, request, token):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["organization"] not in self._get_org_qs(token):
            raise ValidationError({"organization": "Invalid organization"})
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True, methods=["post"], url_path="update-contact/(?P<contact_id>[^/.]+)"
    )
    def update_contact(self, request, token, contact_id):
        contact = get_object_or_404(self._get_contacts_qs(token), id=contact_id)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(contact, data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["organization"] not in self._get_org_qs(token):
            raise ValidationError({"organization": "Invalid organization"})
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_event_qs(self, token):
        invitation = self.get_invitation(token)
        if invitation.event:
            return [invitation.event]
        return invitation.event_group.events.all()

    @action(detail=True, methods=["get"])
    def events(self, request, token):
        # Get the invitation using the token from the URL
        serializer_class = self.get_serializer_class()
        return Response(serializer_class(self._get_event_qs(token), many=True).data)

    def _get_org_qs(self, token):
        invitation = self.get_invitation(token)
        if invitation.organization:
            results = [invitation.organization]
        else:
            results = Organization.objects.filter(
                government=invitation.country,
                organization_type__acronym="GOV",
            ).prefetch_related("country", "government")
        return results

    @action(detail=True, methods=["get"])
    def organizations(self, request, token):
        serializer_class = self.get_serializer_class()
        return Response(serializer_class(self._get_org_qs(token), many=True).data)

    @action(detail=True, methods=["get"])
    def roles(self, request, token):
        self.get_invitation(token)
        return Response(RegistrationRole.objects.all().values_list("name", flat=True))
