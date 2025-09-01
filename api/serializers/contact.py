from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
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
    organization_type = serializers.SlugRelatedField("acronym", read_only=True)

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
    has_photo = serializers.SerializerMethodField()
    country_name = serializers.SlugRelatedField(
        "name", source="country", read_only=True
    )

    class Meta:
        model = Contact
        fields = (
            "id",
            "title",
            "gender",
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
            "has_photo",
            "department",
            "designation",
            # Address
            "country_name",
            "country",
            "city",
            "state",
            "postal_code",
            "address",
            "is_use_organization_address",
        )

    def get_has_photo(self, obj) -> bool:
        return bool(obj.photo)

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            try:
                instance.clean_for_nomination()
                instance.clean()
            except DjangoValidationError as e:
                raise ValidationError(e.message_dict) from e
            return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            try:
                instance.clean_for_nomination()
                instance.clean()
            except DjangoValidationError as e:
                raise ValidationError(e.message_dict) from e
            return instance


class ContactDetailSerializer(ContactSerializer):
    """Contact serializer with nested organization details."""

    organization = OrganizationSerializer(read_only=True)
