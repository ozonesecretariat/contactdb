from rest_framework import serializers

from core.models import Contact, Country, Organization


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("code", "name", "official_name")


class OrganizationSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    government = CountrySerializer(read_only=True)

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "acronym",
            "organization_type",
            "government",
            "country",
            "state",
            "city",
            "postal_code",
            "address",
            "phones",
            "faxes",
            "websites",
            "emails",
        )


class ContactSerializer(serializers.ModelSerializer):
    """
    Basic Contact serializer with no detailed organization info, to be used in
    events nominations.
    """

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


class ContactDetailSerializer(ContactSerializer):
    """Contact serializer with nested organization details."""

    organization = OrganizationSerializer(read_only=True)
