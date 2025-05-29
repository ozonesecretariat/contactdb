from rest_framework import serializers

from api.serializers.country import CountrySerializer
from core.models import Contact
from events.models import Event, EventGroup, Registration


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
        fields = ("id", "event", "organization", "contact", "created_on", "status")
        read_only_fields = ("created_on", "status")
