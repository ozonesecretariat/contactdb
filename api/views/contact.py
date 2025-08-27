from django.http import FileResponse
from rest_framework import mixins, viewsets
from rest_framework.decorators import action

from api.serializers.contact import ContactSerializer
from core.models import Contact


class ContactViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = ContactSerializer
    queryset = Contact.objects.all()

    @action(detail=True)
    def photo(self, request, pk):
        return FileResponse(self.get_object().photo.open("rb"))
