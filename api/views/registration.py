from rest_framework import mixins, viewsets

from api.serializers.event import RegistrationStatusSerializer
from events.models import Registration


class RegistrationStatusViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Registration.objects.all()
    serializer_class = RegistrationStatusSerializer
