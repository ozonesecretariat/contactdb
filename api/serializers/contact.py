from rest_framework import serializers

from core.models import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ("id", "first_name", "last_name", "emails")
