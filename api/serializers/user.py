import dj_rest_auth.serializers
from constance import config
from django.conf import settings
from rest_framework import serializers
from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Used to get basic info for the current user
    """

    roles = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "is_superuser",
            "is_active",
            "is_staff",
            "two_factor_enabled",
            "roles",
            "permissions",
        )
        read_only_fields = ("email", "is_superuser", "is_active", "is_staff")

    def get_permissions(self, obj) -> list[str]:
        return list(obj.get_all_permissions())


class PasswordResetSerializer(dj_rest_auth.serializers.PasswordResetSerializer):
    def get_email_options(self):
        return {
            "domain_override": settings.MAIN_FRONTEND_HOST,
        }
