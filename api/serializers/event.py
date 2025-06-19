from rest_framework import serializers

from api.serializers.contact import OrganizationSerializer
from api.serializers.country import CountrySerializer
from core.models import Contact
from events.models import (
    Event,
    EventGroup,
    Registration,
    RegistrationRole,
)


class ContactSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = Contact
        fields = (
            "id",
            "first_name",
            "last_name",
            "emails",
            "organization",
            "full_name",
        )


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
    status = serializers.SlugRelatedField(slug_field="name", read_only=True)
    role = serializers.SlugRelatedField(slug_field="name", queryset=RegistrationRole.objects.all())

    class Meta:
        model = Registration
        fields = ("id", "event", "contact", "created_at", "status", "role")
        read_only_fields = ("created_at", "status")


class NominationSerializer(serializers.ModelSerializer):
    """
    Contains all required fields for nominating contacts.

    If some fields are required by business logic but not by DB constraints,
    they should be added here.
    """

    event = serializers.SlugRelatedField(slug_field="code", queryset=Event.objects.all())
    role = serializers.SlugRelatedField(slug_field="name", queryset=RegistrationRole.objects.all())
    contact = serializers.PrimaryKeyRelatedField(queryset=Contact.objects.all())

    class Meta:
        model = Registration
        fields = ("event", "contact", "role")
        validators = []  #Disables auto-added UniqueTogetherValidator
