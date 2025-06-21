import mimetypes
import uuid

from django.http import FileResponse, HttpResponse
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import PhotoAccessPermission, PhotoUploadPermission
from core.models import Contact


class SecurePhotoView(APIView):
    permission_classes = [PhotoAccessPermission]

    def get(self, request, photo_token):
        try:
            contact = Contact.objects.get(photo_access_uuid=photo_token)
        except Contact.DoesNotExist:
            return Response(status=404)

        if not contact.photo:
            return Response(status=404)

        content_type = mimetypes.guess_type(contact.photo.name)[0] or "image/jpeg"
        response = FileResponse(contact.photo.open("rb"), content_type=content_type)
        response["Cache-Control"] = "private, max-age=3600"
        return response


class PhotoUploadView(APIView):
    permission_classes = [PhotoUploadPermission]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        contact_id = request.data.get("contact_id")
        photo_file = request.FILES.get("photo")

        if not photo_file or not contact_id:
            return HttpResponse({"error": "Missing required fields"}, status=400)

        try:
            contact = Contact.objects.get(id=contact_id)
        except Contact.DoesNotExist:
            return HttpResponse({"error": "Invalid contact"}, status=400)

        # Save the photo and re-generate the UUID
        contact.photo.save(photo_file.name, photo_file, save=True)
        contact.photo_access_uuid = uuid.uuid4()
        contact.save()

        return Response(
            {
                "message": "Photo uploaded successfully",
                "photo_token": str(contact.photo_access_uuid),
            },
            status=201,
        )
