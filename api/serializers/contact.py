from django.urls import reverse
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

    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = (
            "id",
            "title",
            "first_name",
            "last_name",
            "emails",
            "email_ccs",
            "organization",
            "full_name",
            "phones",
            "mobiles",
            "photo_url",
        )

    def get_photo_url(self, obj):
        if not obj.photo or not obj.photo_access_uuid:
            return None
        request = self.context.get("request")
        nomination_token = self.context.get("nomination_token")
        photo_url = reverse(
            "secure-photo", kwargs={"photo_token": obj.photo_access_uuid}
        )
        if nomination_token:
            photo_url = f"{photo_url}?nomination_token={nomination_token}"
        if request:
            return request.build_absolute_uri(photo_url)
        return photo_url


class ContactDetailSerializer(ContactSerializer):
    """Contact serializer with nested organization details."""

    organization = OrganizationSerializer(read_only=True)
