from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Subquery
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from api.serializers.contact import (
    ContactDetailSerializer,
    ContactSerializer,
    CountrySerializer,
    OrganizationSerializer,
)
from api.serializers.event import (
    EventSerializer,
    NominationSerializer,
    RegistrationSerializer,
)
from core.models import Contact, Organization
from events.models import (
    Country,
    Event,
    EventInvitation,
    PriorityPass,
    Registration,
    RegistrationRole,
)


class EventNominationViewSet(ViewSet):
    permission_classes = [AllowAny]
    lookup_field = "token"

    def get_invitation(self, token) -> EventInvitation:
        invitation = get_object_or_404(EventInvitation, token=token)
        invitation.link_accessed = True
        invitation.save()
        return invitation

    def get_queryset(self):
        # Get the invitation using the token from the URL
        token = self.kwargs[self.lookup_field]
        return Registration.objects.select_related(
            "role",
            "event",
            "event__group",
            "event__venue_country",
            "contact",
            "contact__organization",
            "contact__organization__country",
            "contact__organization__government",
        ).filter(
            contact__organization_id__in=Subquery(self._get_org_qs(token).values("id")),
            event_id__in=Subquery(self._get_event_qs(token).values("id")),
        )

    def _get_event_qs(self, token):
        invitation = self.get_invitation(token)
        qs = (
            Event.objects.all()
            .filter(hide_for_nomination=False)
            .select_related("venue_country", "group")
        )
        if invitation.event_group_id:
            qs = qs.filter(group__id=invitation.event_group_id)
        else:
            qs = qs.filter(id=invitation.event_id)
        return qs

    def _get_complete_event_qs(self, token):
        """Does not filter by hide_for_nomination; useful in certain scenarios."""
        invitation = self.get_invitation(token)
        qs = Event.objects.all().select_related("venue_country", "group")
        if invitation.event_group_id:
            qs = qs.filter(group__id=invitation.event_group_id)
        else:
            qs = qs.filter(id=invitation.event_id)
        return qs

    def _get_org_qs(self, token):
        invitation = self.get_invitation(token)
        qs = Organization.objects.all().select_related("country", "government")
        if invitation.country_id:
            qs = qs.filter(government_id=invitation.country_id)
        else:
            qs = qs.filter(id=invitation.organization_id)
        return qs

    def _get_contacts_qs(self, token):
        return (
            Contact.objects.all()
            .filter(organization_id__in=Subquery(self._get_org_qs(token).values("id")))
            .select_related(
                "organization", "organization__country", "organization__government"
            )
        )

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
            "countries": CountrySerializer,
        }
        return serializer_map[self.action]

    def retrieve(self, request, token):
        registrations = self.get_queryset()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(registrations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="available-contacts")
    def available_contacts(self, request, token):
        """List contacts that can be nominated from this organization."""
        serializer_class = self.get_serializer_class()
        return Response(serializer_class(self._get_contacts_qs(token), many=True).data)

    def _create_hidden_event_registrations(self, contact, event_group, priority_pass):
        """
        Helper method to create placeholder registrations for all hidden events
        belonging to the supplied EventGroup.
        """
        if not event_group:
            return []

        hidden_events = event_group.events.filter(hide_for_nomination=True).exclude(
            registrations__contact=contact
        )

        created_registrations = []
        for hidden_event in hidden_events:
            registration, created = Registration.objects.get_or_create(
                contact=contact,
                event=hidden_event,
                defaults={
                    "status": "",
                    "role": None,
                    "organization": contact.organization,
                    "designation": contact.designation or "",
                    "department": contact.department or "",
                    "priority_pass": priority_pass,
                },
            )

            # If the registration already existed, simply update the relevant fields
            if not created:
                registration.organization = contact.organization
                registration.designation = contact.designation or ""
                registration.department = contact.department or ""
                registration.priority_pass = priority_pass
                registration.save(
                    update_fields=[
                        "organization",
                        "designation",
                        "department",
                        "priority_pass",
                    ]
                )

            created_registrations.append(registration)

        return created_registrations

    def _delete_related_hidden_registrations(self, contact, deleted_event_group):
        """
        Helper method to delete all placeholder registrations for this contact
        to events in the same event group.
        Deletion should only happen if contact is no longer registered to any
        "visible" event.
        """
        if not deleted_event_group:
            return

        # Check whether contact has any other visible-event registrations in this group
        has_other_visible_registrations = Registration.objects.filter(
            contact=contact,
            event__group=deleted_event_group,
            event__hide_for_nomination=False,
        ).exists()

        if not has_other_visible_registrations:
            Registration.objects.filter(
                contact=contact,
                event__group=deleted_event_group,
                event__hide_for_nomination=True,
                status="",
            ).delete()

    @action(
        detail=True,
        methods=["post"],
        url_path="nominate-contact/(?P<contact_id>[^/.]+)",
    )
    def nominate_contact(self, request, token, contact_id):
        """Update nomination status for a contact for all the events of the group.

        Any events not specified will have their nomination removed.
        """
        contact = get_object_or_404(self._get_contacts_qs(token), id=contact_id)
        try:
            contact.clean_for_nomination()
        except DjangoValidationError as e:
            raise ValidationError(
                {
                    "contact": (
                        "Contact does not have all the required data, "
                        "please edit in the required details before nominating."
                    )
                }
            ) from e

        available_events = set(self._get_event_qs(token))

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # Including hidden events so we can find any existing nomination to this group
        # and reuse its priority pass
        all_available_events = set(self._get_complete_event_qs(token))
        current_nominations = {
            n.event: n
            for n in contact.registrations.filter(event__in=all_available_events)
        }

        if not current_nominations:
            priority_pass = PriorityPass.objects.create()
        else:
            priority_pass = list(current_nominations.values())[0].priority_pass

        # This allows us to keep track of all event groups to which contact is nominated
        new_visible_event_groups = set()

        with transaction.atomic():
            for nomination in serializer.validated_data:
                event = nomination["event"]
                if event not in available_events:
                    raise ValidationError(
                        {"event": "Contact cannot be nominated in this event"}
                    )
                if contact != nomination["contact"]:
                    raise ValidationError(
                        {"contact": "Contact cannot be nominated by another contact"}
                    )

                try:
                    registration = current_nominations.pop(event)
                    is_new_registration = False
                except KeyError:
                    registration = Registration(
                        event=event,
                        contact=contact,
                    )
                    is_new_registration = True

                if (
                    registration.status != Registration.Status.NOMINATED
                    and registration.role != nomination["role"]
                ):
                    raise ValidationError({"status": "Registration cannot be updated."})

                registration.role = nomination["role"]
                registration.organization = contact.organization
                registration.department = contact.department
                registration.designation = contact.designation
                registration.priority_pass = priority_pass
                registration.save()

                if is_new_registration and event.group:
                    new_visible_event_groups.add(event.group)

            # Anything left of the current nominations that was not provided
            # needs to be removed.
            deleted_visible_event_groups = set()
            for registration in current_nominations.values():
                if registration.status != Registration.Status.NOMINATED:
                    raise ValidationError({"status": "Registration cannot be removed."})
                if registration.event.group:
                    deleted_visible_event_groups.add(registration.event.group)
                registration.delete()

            # Now create hidden registrations for all newly-added "visible" event groups,
            # using the same priority pass.
            for event_group in new_visible_event_groups:
                self._create_hidden_event_registrations(
                    contact, event_group, priority_pass
                )

            # And clean up hidden registrations if no "visible" event attended anymore
            for deleted_event_group in deleted_visible_event_groups:
                self._delete_related_hidden_registrations(contact, deleted_event_group)

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
        serializer = serializer_class(contact, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["organization"] not in self._get_org_qs(token):
            raise ValidationError({"organization": "Invalid organization"})
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def events(self, request, token):
        # Get the invitation using the token from the URL
        serializer_class = self.get_serializer_class()
        return Response(serializer_class(self._get_event_qs(token), many=True).data)

    @action(detail=True, methods=["get"])
    def organizations(self, request, token):
        serializer_class = self.get_serializer_class()
        return Response(serializer_class(self._get_org_qs(token), many=True).data)

    @action(detail=True, methods=["get"])
    def roles(self, request, token):
        self.get_invitation(token)
        return Response(
            RegistrationRole.objects.filter(hide_for_nomination=False).values_list(
                "name", flat=True
            )
        )

    @action(detail=True, methods=["get"])
    def countries(self, request, token):
        self.get_invitation(token)
        serializer_class = self.get_serializer_class()
        return Response(serializer_class(Country.objects.all(), many=True).data)
