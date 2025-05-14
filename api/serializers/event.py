from rest_framework import serializers

from api.serializers.country import CountrySerializer
from events.models import Event


class EventSerializer(serializers.ModelSerializer):
    venue_country = CountrySerializer()

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
        )
