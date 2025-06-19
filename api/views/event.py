from functools import lru_cache

from django.utils import timezone
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from api.permissions import ContactNominationPermission
from api.serializers.contact import (
    ContactDetailSerializer,
    ContactSerializer,
    OrganizationSerializer,
)
from api.serializers.event import (
    EventSerializer,
    NominateContactsSerializer,
    RegistrationSerializer,
)
from core.models import Contact, Organization
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


class EventNominationViewSet(ViewSet):
    permission_classes = [AllowAny, ContactNominationPermission]
    lookup_field = "token"

    def get_invitation(self, token) -> EventInvitation:
        return get_object_or_404(EventInvitation, token=token)

    def get_organization_context(self):
        """
        Used to provide organization context for permission checking
        (ContactNominationPermission needs it ).
        """
        try:
            token = self.kwargs[self.lookup_field]
            invitation = self.get_invitation(token)
            return invitation.organization
        except (KeyError, EventInvitation.DoesNotExist):
            return None

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
        Return appropriate serializer based on action
        """
        serializer_map = {
            "retrieve": RegistrationSerializer,
            "available_contacts": ContactDetailSerializer,
            "create_contact": ContactSerializer,
            "nominate_contacts": RegistrationSerializer,
            "events": EventSerializer,
            "organizations": OrganizationSerializer,
        }
        return serializer_map.get(self.action, RegistrationSerializer)

    def retrieve(self, request, token):
        registrations = self.get_queryset()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(registrations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="available-contacts")
    def available_contacts(self, request, token):
        """List contacts that can be nominated from this organization."""
        serializer_class = self.get_serializer_class()

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
        serializer = serializer_class(
            query,
            many=True,
            context={"nomination_token": token, "request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="nominate-contacts")
    def nominate_contacts(self, request, token):
        # Get the invitation using the token from the URL
        invitation = self.get_invitation(token)

        data_serializer = NominateContactsSerializer(
            data=request.data, context={"invitation": invitation}
        )
        data_serializer.is_valid(raise_exception=True)

        events = Event.objects.filter(code__in=data_serializer.validated_data["events"])
        nominations = data_serializer.validated_data["nominations"]

        registrations = []
        for event in events:
            for nomination in nominations:
                registration = Registration.objects.create(
                    event=event,
                    contact=nomination["contact"],
                    status_id=get_nomination_status_id(),
                    role=nomination["role"],
                    is_funded=nomination["is_funded"],
                    priority_pass_code=nomination.get("priority_pass_code", ""),
                    date=timezone.now(),
                )
                registrations.append(registration)

        serializer_class = self.get_serializer_class()
        return Response(serializer_class(registrations, many=True).data)

    @action(detail=True, methods=["post"], url_path="create-contact")
    def create_contact(self, request, token):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["organization"] not in self._get_org_qs(token):
            raise ValidationError({"organization": "Invalid organization"})
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def events(self, request, token):
        # Get the invitation using the token from the URL
        invitation = self.get_invitation(token)

        # TODO: this assumes mutual exclusion between event and event_group
        if invitation.event:
            events = [invitation.event]
        else:
            events = invitation.event_group.events.all()
        serializer_class = self.get_serializer_class()
        return Response(serializer_class(events, many=True).data)

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
