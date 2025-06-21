import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse as django_reverse

from api.serializers.contact import ContactSerializer
from api.tests.base import BaseAPITestCase
from api.tests.factories import (
    ContactFactory,
    EventInvitationFactory,
    OrganizationFactory,
)


class TestPhotoAPI(BaseAPITestCase):
    fixtures = [
        *BaseAPITestCase.fixtures,
        "initial/region",
        "initial/subregion",
        "initial/country",
        "test/eventgroup",
        "test/event",
    ]

    def setUp(self):
        self.organization = OrganizationFactory()
        self.contact = ContactFactory(organization=self.organization)
        self.invitation = EventInvitationFactory(organization=self.organization)
        self.photo_token = str(self.contact.photo_access_uuid)
        self.photo_url = django_reverse(
            "secure-photo", kwargs={"photo_token": self.photo_token}
        )
        self.upload_url = django_reverse("photo-upload")

    def test_photo_access_staff(self):
        self.login_admin()
        # Upload a photo first
        self.contact.photo.save(
            "test.jpg", SimpleUploadedFile("test.jpg", b"abc"), save=True
        )
        response = self.client.get(self.photo_url)
        self.assertEqual(response.status_code, 200)

    def test_photo_access_with_valid_token(self):
        # Upload a photo first
        self.contact.photo.save(
            "test.jpg", SimpleUploadedFile("test.jpg", b"abc"), save=True
        )
        url = f"{self.photo_url}?nomination_token={self.invitation.token}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_photo_access_invalid_token(self):
        # Upload a photo first
        self.contact.photo.save(
            "test.jpg", SimpleUploadedFile("test.jpg", b"abc"), save=True
        )
        url = f"{self.photo_url}?nomination_token={uuid.uuid4()}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_photo_access_org_mismatch(self):
        other_org = OrganizationFactory()
        other_invitation = EventInvitationFactory(organization=other_org)
        self.contact.photo.save(
            "test.jpg", SimpleUploadedFile("test.jpg", b"abc"), save=True
        )
        url = f"{self.photo_url}?nomination_token={other_invitation.token}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_photo_upload_staff(self):
        self.login_admin()
        file = SimpleUploadedFile("photo.jpg", b"abc", content_type="image/jpeg")
        response = self.client.post(
            self.upload_url, {"contact_id": self.contact.id, "photo": file}
        )
        self.assertEqual(response.status_code, 201)
        self.contact.refresh_from_db()
        self.assertTrue(self.contact.photo)

    def test_photo_upload_with_valid_token(self):
        file = SimpleUploadedFile("photo.jpg", b"abc", content_type="image/jpeg")
        response = self.client.post(
            self.upload_url,
            {
                "contact_id": self.contact.id,
                "photo": file,
                "nomination_token": self.invitation.token,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.contact.refresh_from_db()
        self.assertTrue(self.contact.photo)

    def test_photo_upload_invalid_token(self):
        file = SimpleUploadedFile("photo.jpg", b"abc", content_type="image/jpeg")
        response = self.client.post(
            self.upload_url,
            {
                "contact_id": self.contact.id,
                "photo": file,
                "nomination_token": uuid.uuid4(),
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_photo_url_in_serializer(self):
        self.contact.photo.save(
            "test.jpg", SimpleUploadedFile("test.jpg", b"abc"), save=True
        )
        # Simulate serializer context as passed in the nomination-related view
        serializer = ContactSerializer(
            self.contact,
            context={"nomination_token": self.invitation.token, "request": None},
        )
        url = serializer.data["photo_url"]
        self.assertIn(str(self.contact.photo_access_uuid), url)
        self.assertIn(str(self.invitation.token), url)
