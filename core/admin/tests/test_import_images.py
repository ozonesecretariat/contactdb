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
        self.assertEqual(response.context_data["contact_count"], 1)
        self.assertEqual(
            response.context_data["total_contacts"], Contact.objects.count()
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
                "import_scope": "selected",
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
        queryset = Contact.objects.filter(id=self.contact_with_kronos.id)

        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "import_scope": "all",
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
        self.assertIsNone(task.contact_ids)
        self.assertFalse(task.overwrite_existing)

    def test_import_photos_with_overwrite_enabled(self):
        """Test importing photos with overwrite option enabled."""
        queryset = Contact.objects.filter(id=self.contact_with_photo.id)

        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "import_scope": "selected",
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
                "import_scope": "selected",
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
                "import_scope": "selected",
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
        expected_message = (
            f"Photo import task {task.id} started for 1 contact(s)"
        )
        self.assertIn(expected_message, str(messages[0]))

    def test_import_photos_all_contacts_message(self):
        """Test success message for all contacts import."""
        queryset = Contact.objects.filter(id=self.contact_with_kronos.id)

        request = self.factory.post(
            "/fake-url/",
            {
                "apply": "1",
                "import_scope": "all",
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
                "import_scope": "selected",
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

        request = self.factory.get("/fake-url/", {"action": "import_photos_from_kronos"})
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        response = self.admin.import_photos_from_kronos(request, queryset)

        context = response.context_data
        self.assertEqual(context["title"], "Import Contact Photos from Kronos")
        self.assertEqual(context["contact_count"], 2)
        self.assertEqual(context["total_contacts"], Contact.objects.count())

    def test_action_requires_change_permission(self):
        """Test that the action requires change permission."""
        # Check that action has correct permission requirement
        action_func = self.admin.import_photos_from_kronos
        self.assertTrue(hasattr(action_func, "allowed_permissions"))
        self.assertIn("change", action_func.allowed_permissions)

    def test_action_description(self):
        """Test that action has correct description."""
        action_func = self.admin.import_photos_from_kronos
        self.assertEqual(action_func.short_description, "Import photos from Kronos")
