from rest_framework import serializers

from events.models import DSA


class DSASerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    number_of_days = serializers.ReadOnlyField()
    dsa_on_arrival = serializers.ReadOnlyField()
    total_dsa = serializers.ReadOnlyField()

    class Meta:
        model = DSA
        fields = (
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
