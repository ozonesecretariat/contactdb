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
    valid_date_range = serializers.SerializerMethodField()

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
        )

    def get_badge_url(self, obj: PriorityPass):
        return reverse("admin:badge_view", args=[obj.id]) + "?pdf=true"

    def get_valid_date_range(self, obj: PriorityPass):
        date_fmt = "%b %e, %Y"
        start, end = obj.valid_from, obj.valid_to

        if not start and not end:
            return ""

        if start == end or (bool(start) ^ bool(end)):
            return (start or end).strftime(date_fmt)

        if end < start:
            start, end = end, start

        same_year = start.year == end.year
        same_month = start.month == end.month

        if same_year and same_month:
            return "{month} {start_day}-{end_day}, {year} ".format(
                month=start.strftime("%b"),
                start_day=start.day,
                end_day=end.day,
                year=start.year,
            )

        if same_year:
            return "{start_month} {start_day} - {end_month} {end_day}, {year} ".format(
                start_month=start.strftime("%b"),
                start_day=start.day,
                end_month=end.strftime("%b"),
                end_day=end.day,
                year=start.year,
            )

        return "{start_date} to {end_date}".format(
            start_date=start.strftime(date_fmt),
            end_date=end.strftime(date_fmt),
        )
