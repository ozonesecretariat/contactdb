from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

from api.tests.factories import ContactFactory
from core.admin.contact import ContactAdmin
from core.models import Contact, ImportContactPhotosTask


class TestContactAdminPhotoImport(TestCase):
    fixtures = [
        "initial/region",
        "initial/subregion",
        "initial/country",
    ]

    def setUp(self):
        self.site = AdminSite()
        self.admin = ContactAdmin(Contact, self.site)
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="password"
        )

        # Create test contacts
        self.contact_with_kronos = ContactFactory(
            first_name="John",
            last_name="Doe",
            contact_ids=["kronos123", "kronos456"],
        )
        self.contact_without_kronos = ContactFactory(
            first_name="Jane",
            last_name="Smith",
            contact_ids=None,
        )
        self.contact_with_photo = ContactFactory(
            first_name="Bob",
            last_name="Wilson",
            contact_ids=["kronos789"],
            photo="existing_photo.jpg",
        )
        self.all_contacts_ids = list(Contact.objects.values_list("id", flat=True))

        self.mock_contact_data = {
            "contactId": "kronos123",
            "createdOn": "2023-01-01T10:00:00Z",
            "updatedOn": "2023-06-15T14:30:00Z",
            "updatedBy": "admin",
        }

        self.mock_photo_data = {
            "contactId": "kronos123",
            "date": "2023-06-15T14:30:00Z",
            "src": "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
        }
        self.mock_empty_photo_data = None

    def test_import_photos_get_request_shows_form(self):
        """Test that GET request shows the import form."""
        queryset = Contact.objects.filter(id=self.contact_with_kronos.id)

        request = self.factory.get(
            "/fake-url/", {"action": "import_photos_from_kronos"}
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        response = self.admin.import_photos_from_kronos(request, queryset)

        # Should return intermediate response with template
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Import Contact Photos from Kronos", response.context_data["title"]
        )

    def test_import_photos_selected_contacts_only(self):
        """Test importing photos for selected contacts only."""
        queryset = Contact.objects.filter(
            id__in=[self.contact_with_kronos.id, self.contact_without_kronos.id]
        )

        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "overwrite": "",
            },
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        response = self.admin.import_photos_from_kronos(request, queryset)

        # Should create task with selected contact IDs
        self.assertIsNone(response)

        task = ImportContactPhotosTask.objects.first()
        self.assertIsNotNone(task)
        self.assertFalse(task.overwrite_existing)
        self.assertEqual(
            set(task.contact_ids),
            {self.contact_with_kronos.id, self.contact_without_kronos.id},
        )

    def test_import_photos_all_contacts(self):
        """Test importing photos for all contacts."""
        queryset = Contact.objects.all()

        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "overwrite": "",
            },
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        response = self.admin.import_photos_from_kronos(request, queryset)

        # Should create task with contact_ids=None (all contacts)
        self.assertIsNone(response)

        task = ImportContactPhotosTask.objects.first()
        self.assertIsNotNone(task)
        self.assertEqual(task.contact_ids, self.all_contacts_ids)
        self.assertFalse(task.overwrite_existing)

    def test_import_photos_with_overwrite_enabled(self):
        """Test importing photos with overwrite option enabled."""
        queryset = Contact.objects.filter(id=self.contact_with_photo.id)

        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "overwrite": "on",
            },
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.import_photos_from_kronos(request, queryset)

        task = ImportContactPhotosTask.objects.first()
        self.assertIsNotNone(task)
        self.assertTrue(task.overwrite_existing)
        self.assertEqual(task.contact_ids, [self.contact_with_photo.id])

    @patch("core.models.ImportContactPhotosTask.run")
    def test_import_photos_task_execution(self, mock_run):
        """Test that the task is executed asynchronously."""
        queryset = Contact.objects.filter(id=self.contact_with_kronos.id)

        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "overwrite": "",
            },
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.import_photos_from_kronos(request, queryset)

        # Verify task was created and run called
        task = ImportContactPhotosTask.objects.first()
        self.assertIsNotNone(task)
        mock_run.assert_called_once_with(is_async=True)

    def test_import_photos_success_message(self):
        """Test that appropriate success message is shown."""
        queryset = Contact.objects.filter(id=self.contact_with_kronos.id)

        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "overwrite": "",
            },
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        # Capture messages
        self.admin.import_photos_from_kronos(request, queryset)

        # Check success message was added
        messages = list(request._messages)
        self.assertEqual(len(messages), 1)

        task = ImportContactPhotosTask.objects.first()
        expected_message = f"Photo import task {task.id} started for 1 contact(s)"
        self.assertIn(expected_message, str(messages[0]))

    def test_import_photos_all_contacts_message(self):
        """Test success message for all contacts import."""
        queryset = Contact.objects.all()

        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "overwrite": "",
            },
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.import_photos_from_kronos(request, queryset)

        messages = list(request._messages)
        task = ImportContactPhotosTask.objects.first()
        total_contacts = Contact.objects.count()
        expected_message = (
            f"Photo import task {task.id} started for {total_contacts} contact(s)"
        )
        self.assertIn(expected_message, str(messages[0]))

    def test_import_photos_empty_queryset(self):
        """Test importing photos with empty queryset."""
        queryset = Contact.objects.none()

        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "overwrite": "",
            },
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.import_photos_from_kronos(request, queryset)

        task = ImportContactPhotosTask.objects.first()
        self.assertEqual(task.contact_ids, [])

    def test_import_photos_template_context(self):
        """Test template context variables."""
        queryset = Contact.objects.filter(
            id__in=[self.contact_with_kronos.id, self.contact_without_kronos.id]
        )

        request = self.factory.get(
            "/fake-url/", {"action": "import_photos_from_kronos"}
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        response = self.admin.import_photos_from_kronos(request, queryset)

        context = response.context_data
        self.assertEqual(context["title"], "Import Contact Photos from Kronos")

    def test_action_requires_change_permission(self):
        """Test that the action requires change permission."""
        self.assertTrue(
            hasattr(self.admin.import_photos_from_kronos, "allowed_permissions")
        )
        self.assertIn(
            "change", self.admin.import_photos_from_kronos.allowed_permissions
        )

        user_no_perms = get_user_model().objects.create_user(
            email="impermisibilul@permisiuni.com", password="parola"
        )

        request = self.factory.get("/admin/core/contact/")
        request.user = user_no_perms

        # Get available actions for this user
        actions = self.admin.get_actions(request)

        # Action should not be available
        self.assertNotIn("import_photos_from_kronos", actions)

    def test_action_description(self):
        """Test that action has correct description."""
        action_func = self.admin.import_photos_from_kronos
        self.assertEqual(action_func.short_description, "Import photos from Kronos")

    def test_overwrite_enabled_by_default(self):
        """Test that photos overwrite is enabled by default."""
        queryset = Contact.objects.filter(id=self.contact_with_kronos.id)

        # Creating request with no "overwrite" param
        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
            },
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.import_photos_from_kronos(request, queryset)

        task = ImportContactPhotosTask.objects.first()
        self.assertTrue(task.overwrite_existing)

    @patch("events.kronos.KronosClient.get_contact_data")
    @patch("events.kronos.KronosClient.get_contact_photo")
    @patch("events.kronos.KronosClient._login")
    def test_job_execution(
        self, mock_login, mock_get_contact_photo, mock_get_contact_data
    ):
        """Test that job executes correctly with mocked API responses."""
        # Setup mocks
        mock_get_contact_data.return_value = self.mock_contact_data
        mock_get_contact_photo.return_value = self.mock_photo_data

        queryset = Contact.objects.filter(id=self.contact_with_kronos.id)
        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "overwrite": "on",
            },
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        # Trigger admin action & execute jos synchronously
        self.admin.import_photos_from_kronos(request, queryset)

        task = ImportContactPhotosTask.objects.first()
        task.run(is_async=False)

        # Verifying that the API was "called" and photo was added
        mock_get_contact_data.assert_any_call("kronos123")
        mock_get_contact_data.assert_any_call("kronos456")
        mock_get_contact_photo.assert_called_with("kronos123")

        self.contact_with_kronos.refresh_from_db()
        self.assertTrue(self.contact_with_kronos.photo)

    @patch("events.kronos.KronosClient._login")
    def test_job_execution_no_contacts_found(self, mock_login):
        """
        Test job execution when no contacts match the query.

        The other API calls are intentionally not mocked - will fail if called.
        """
        queryset = Contact.objects.filter(id=self.contact_without_kronos.id)

        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "overwrite": "on",
            },
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.import_photos_from_kronos(request, queryset)

        task = ImportContactPhotosTask.objects.first()
        task.run(is_async=False)

        # Verify no processing occurred
        task.refresh_from_db()
        self.assertIn("Processed 0 contacts, imported 0 photos", task.description)

    @patch("events.kronos.KronosClient.get_contact_data")
    @patch("events.kronos.KronosClient.get_contact_photo")
    @patch("events.kronos.KronosClient._login")
    def test_job_execution_multiple_kronos_ids_and_photos(
        self, mock_login, mock_get_photo, mock_get_data
    ):
        """
        Test that most recent Kronos ID is used when multiple photos exist.
        """

        # This needs slightly more cxomplex fixtures than the default.
        # kronos456 is more recent, has photo; kronos123 is older, no photo
        def mock_contact_data(kronos_id):
            return {
                "contactId": kronos_id,
                "createdOn": "2023-01-01T10:00:00Z",
                "updatedOn": (
                    "2023-06-15T14:30:00Z"
                    if kronos_id == "kronos456"
                    else "2023-06-10T14:30:00Z"
                ),
                "updatedBy": "admin",
            }

        def mock_photo_data(kronos_id):
            if kronos_id == "kronos456":
                return {
                    "contactId": kronos_id,
                    "src": "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                }
            if kronos_id == "kronos123":
                return None
            return None

        mock_get_data.side_effect = mock_contact_data
        mock_get_photo.side_effect = mock_photo_data

        queryset = Contact.objects.filter(id=self.contact_with_kronos.id)

        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "overwrite": "on",
            },
        )
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.import_photos_from_kronos(request, queryset)

        task = ImportContactPhotosTask.objects.first()
        task.run(is_async=False)

        # Asserting expected API calls happened
        mock_get_data.assert_any_call("kronos123")
        mock_get_data.assert_any_call("kronos456")
        mock_get_photo.assert_called_with("kronos456")

        # Verify contact has photo
        self.contact_with_kronos.refresh_from_db()
        self.assertTrue(self.contact_with_kronos.photo)
