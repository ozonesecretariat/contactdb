from rest_framework import serializers

from api.serializers.country import CountrySerializer
from events.models import Event, EventTag


class EventTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTag
        fields = ("name", "description")


class EventSerializer(serializers.ModelSerializer):
    venue_country = CountrySerializer()
    tags = EventTagSerializer(many=True, read_only=True)

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
