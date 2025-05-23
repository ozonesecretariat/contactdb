from rest_framework import serializers

from api.serializers.country import CountrySerializer
from events.models import Event, EventGroup


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
            "tags",
        )
