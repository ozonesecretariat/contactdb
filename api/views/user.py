from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import User
from api.serializers.user import CurrentUserSerializer


class CurrentUserViewSet(APIView):
    serializer_class = CurrentUserSerializer

    def get_object(self):
        return User.objects.get(id=self.request.user.pk)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance)
        return Response(serializer.data)
