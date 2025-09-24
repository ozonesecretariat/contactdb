from rest_framework import serializers

from common.serializers import DateField
from events.models import DSA, Registration


class DSASerializer(serializers.ModelSerializer):
    registration = serializers.PrimaryKeyRelatedField(
        queryset=Registration.objects.all()
    )
    arrival_date = DateField(required=False, allow_blank=True, allow_null=True)
    departure_date = DateField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = DSA
        fields = (
            "registration",
            "id",
            "umoja_travel",
            "bp",
            "arrival_date",
            "departure_date",
            "cash_card",
            "paid_dsa",
            # Encrypted fields
            "boarding_pass",
            "passport",
            "signature",
            # Read-only fields
            "number_of_days",
            "dsa_on_arrival",
            "total_dsa",
        )
        read_only_fields = ("id", "number_of_days", "dsa_on_arrival", "total_dsa")

    def validate(self, attrs):
        result = super().validate(attrs)
        instance = self.Meta.model(**attrs)
        instance.clean()
        return result
