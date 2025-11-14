from rest_framework import viewsets

from api.serializers.dsa import DSASerializer
from events.models import DSA


class DSAViewSet(viewsets.ModelViewSet):
    queryset = DSA.objects.all()
    serializer_class = DSASerializer
