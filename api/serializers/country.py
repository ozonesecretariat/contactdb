from rest_framework import serializers
from core.models import Country


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("code", "name", "official_name")
