from django.urls import reverse
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
    badge_url = serializers.SerializerMethodField()

    class Meta:
        model = PriorityPass
        fields = (
            "code",
            "contact",
            "country",
            "organization",
            "registrations",
            "created_at",
            "badge_url",
            "valid_date_range",
            "is_currently_valid",
        )

    def get_badge_url(self, obj: PriorityPass):
        return reverse("admin:badge_view", args=[obj.id]) + "?pdf=true"
