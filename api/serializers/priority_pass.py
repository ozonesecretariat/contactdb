from rest_framework import serializers

from api.serializers.contact import (
    ContactSerializer,
    CountrySerializer,
    OrganizationSerializer,
)
from api.serializers.event import RegistrationSerializer
from events.models import PriorityPass


class PriorityPassSerializer(serializers.ModelSerializer):
    contact = ContactSerializer(read_only=True)
    country = CountrySerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    registrations = RegistrationSerializer(many=True, read_only=True)

    class Meta:
        model = PriorityPass
        fields = (
            "code",
            "contact",
            "country",
            "organization",
            "registrations",
            "created_at",
        )
