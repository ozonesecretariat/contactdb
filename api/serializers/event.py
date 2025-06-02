from rest_framework import serializers

from api.serializers.country import CountrySerializer
from core.models import Contact
from events.models import Event, EventGroup, Registration, RegistrationRole


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ("id", "first_name", "last_name", "emails")


class EventGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventGroup
        fields = ("name", "description")


class EventSerializer(serializers.ModelSerializer):
    venue_country = CountrySerializer()
    groups = EventGroupSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = (
            "code",
            "title",
            "start_date",
            "end_date",
            "venue_country",
            "venue_city",
            "dates",
            "groups",
        )


class RegistrationSerializer(serializers.ModelSerializer):
    contact = ContactSerializer(read_only=True)
    event = EventSerializer(read_only=True)

    class Meta:
        model = Registration
        fields = ("id", "event", "contact", "created_at", "status")
        read_only_fields = ("created_on", "status")


class NominationSerializer(serializers.Serializer):
    """
    Contains all required fields for nominating contacts.

    If some fields are required by business logic but not by DB constraints,
    they should be added here.
    """

    contact = serializers.PrimaryKeyRelatedField(queryset=Contact.objects.all())
    is_funded = serializers.BooleanField(required=True)
    role = serializers.PrimaryKeyRelatedField(queryset=RegistrationRole.objects.all())
    priority_pass_code = serializers.CharField(required=False, allow_blank=True)


class NominateContactsSerializer(serializers.Serializer):
    """
    "Write" serializer used to validate and convert data for Nominations.

    Relies on an `EvenInvitation` object being inserted into the context.
    """

    events = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of event codes to nominate contacts for",
    )
    nominations = NominationSerializer(many=True)

    def validate_nominations(self, nominations):
        """
        This actually validates that the contact ids in the nominations are valid
        contact ids for the invitation included in the context.
        """
        invitation = self.context["invitation"]
        invalid_contacts = [
            n["contact"]
            for n in nominations
            if n["contact"].organization != invitation.organization
        ]
        if invalid_contacts:
            raise serializers.ValidationError(
                f"Contacts {[c.id for c in invalid_contacts]} do not belong to "
                f"{invitation.organization}"
            )
        return nominations

    def validate_events(self, event_codes):
        invitation = self.context["invitation"]
        valid_events = (
            [invitation.event]
            if invitation.event
            else invitation.event_group.events.all()
        )
        valid_codes = {event.code for event in valid_events}
        invalid_codes = set(event_codes) - valid_codes
        if invalid_codes:
            raise serializers.ValidationError(
                f"Events {invalid_codes} are not valid for this invitation"
            )
        return event_codes
