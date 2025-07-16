import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.urls import reverse
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.serializers import DateField
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

    passport = serializers.JSONField(write_only=True, required=False, allow_null=True)
    credentials = serializers.JSONField(
        write_only=True, required=False, allow_null=True
    )
    nationality = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    passport_number = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    passport_date_of_issue = DateField(
        write_only=True, required=False, allow_blank=True
    )
    passport_date_of_expiry = DateField(
        write_only=True, required=False, allow_blank=True
    )
    photo = Base64ImageField(write_only=True, required=False, allow_null=True)
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
            "has_credentials",
            "needs_visa_letter",
            "passport",
            "credentials",
            "nationality",
            "passport_number",
            "passport_date_of_issue",
            "passport_date_of_expiry",
            "photo",
            "photo_url",
            "department",
            "designation",
            # Address
            "country",
            "city",
            "state",
            "postal_code",
            "address",
            "is_use_organization_address",
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

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            try:
                instance.clean()
            except DjangoValidationError as e:
                raise ValidationError(e.message_dict) from e
            return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if validated_data.get("photo"):
                # Regenerate the UUID so the photo isn't cached
                instance.photo_access_uuid = uuid.uuid4()
                instance.save()
            try:
                instance.clean()
            except DjangoValidationError as e:
                raise ValidationError(e.message_dict) from e
            return instance


class ContactDetailSerializer(ContactSerializer):
    """Contact serializer with nested organization details."""

    organization = OrganizationSerializer(read_only=True)
