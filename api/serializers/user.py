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
    app_settings = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "is_superuser",
            "is_active",
            "is_staff",
            "app_settings",
            "roles",
            "permissions",
        )
        read_only_fields = ("email", "is_superuser", "is_active", "is_staff")

    def get_permissions(self, obj) -> list[str]:
        return list(obj.get_all_permissions())

    def get_app_settings(self, obj) -> dict[str, str]:
        return {
            "sentry_dsn": settings.SENTRY_DSN,
            "environment_name": settings.ENVIRONMENT_NAME,
        }
