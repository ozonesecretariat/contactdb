from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

from api.tests.factories import ContactFactory, EventFactory, OrganizationFactory
from core.models import OrganizationType
from emails.admin import EmailAdmin, InvitationEmailAdmin
from emails.models import Email, InvitationEmail, SendEmailTask
from emails.tests.factories import EmailFactory, InvitationEmailFactory


class TestEmailAdminDrafts(TestCase):
    """Test draft-related functionality in EmailAdmin."""

    fixtures = [
        "initial/country",
        "initial/organizationtype",
        "initial/registrationrole",
    ]

    def setUp(self):
        self.site = AdminSite()
        self.admin = EmailAdmin(Email, self.site)
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_superuser(
            email="drafty-admin@example.com", password="draft-password"
        )

        self.contact = ContactFactory()
        self.event = EventFactory()

    def _make_request(self, method, data=None):
        """HTTP requests helper; avoids too much boilerplate code."""
        if method == "POST":
            request = self.factory.post("/fake-url/", data or {})
        else:
            request = self.factory.get("/fake-url/")

        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_response_add_save_draft(self):
        """Test saving email as draft via save_draft button."""
        email = EmailFactory(
            subject="Test Draft",
            content="Draft content",
            recipients=[self.contact],
            is_draft=False,
        )

        request = self._make_request("POST", data={"_save_draft": "Save Draft"})
        response = self.admin.response_add(request, email)

        # Check email is marked as draft
        email.refresh_from_db()
        self.assertTrue(email.is_draft)

        # Check redirect to the changelist view and that no email tasks were created
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/emails/email", response.url)
        self.assertEqual(SendEmailTask.objects.count(), 0)

    def test_response_add_send_now(self):
        """Test sending existing draft email immediately via _save button."""
        email = EmailFactory(
            subject="Test Send",
            content="Send content",
            recipients=[self.contact],
            is_draft=True,
        )

        request = self._make_request("POST", data={"_save": "Send Email Now"})
        response = self.admin.response_add(request, email)

        # Check email is not a draft and the redirect happens
        email.refresh_from_db()
        self.assertFalse(email.is_draft)
        self.assertEqual(response.status_code, 302)

    def test_response_change_save_draft(self):
        """Test updating existing draft via _save_draft button."""
        email = EmailFactory(
            subject="Existing Draft",
            content="Draft content",
            recipients=[self.contact],
            is_draft=True,
        )

        request = self._make_request("POST", data={"_save_draft": "Save Draft"})
        response = self.admin.response_change(request, email)

        # After save draft, a draft should remain a draft
        email.refresh_from_db()
        self.assertTrue(email.is_draft)

        # Should redirect back to change view
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/emails/email", response.url)

    def test_response_change_send_now(self):
        """Test basic conversion of draft to sent email."""
        email = EmailFactory(
            subject="Convert to Sent directly",
            content="Send content",
            recipients=[self.contact],
            is_draft=True,
        )

        request = self._make_request("POST", data={"_save": "Send Email Now"})
        response = self.admin.response_change(request, email)

        email.refresh_from_db()
        self.assertFalse(email.is_draft)
        self.assertEqual(response.status_code, 302)

    def test_response_post_save_add_draft(self):
        """Saving as draft should leave us in the change page without email sending."""
        email = EmailFactory(
            subject="Draft Email",
            recipients=[self.contact],
            is_draft=True,
        )

        request = self._make_request("POST")
        response = self.admin.response_post_save_add(request, email)

        # Should redirect to change view, no email tasks created
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/admin/emails/email/{email.pk}/change/", response.url)
        self.assertEqual(SendEmailTask.objects.count(), 0)

    def test_response_post_save_add_sent_email(self):
        """Test that response_post_save_add processes sent emails normally."""
        email = EmailFactory(
            subject="Sent Email",
            recipients=[self.contact],
            is_draft=False,
        )

        request = self._make_request("GET")
        response = self.admin.response_post_save_add(request, email)

        # Should create email tasks and redirect them users to task list
        self.assertGreater(SendEmailTask.objects.count(), 0)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/emails/sendemailtask", response.url)

    def test_has_change_permission_draft(self):
        """Test that only drafts can be edited."""
        draft_email = EmailFactory(is_draft=True)
        sent_email = EmailFactory(is_draft=False)

        request = self._make_request("GET")

        self.assertTrue(self.admin.has_change_permission(request, draft_email))
        self.assertFalse(self.admin.has_change_permission(request, sent_email))

    def test_has_delete_permission_draft(self):
        """Tests that only drafts are deletable."""
        draft_email = EmailFactory(is_draft=True)
        sent_email = EmailFactory(is_draft=False)

        request = self._make_request("GET")

        # Deleting drafts should be allowed, but not deleting sent emails
        self.assertTrue(self.admin.has_delete_permission(request, draft_email))
        self.assertFalse(self.admin.has_delete_permission(request, sent_email))

    def test_get_fieldsets_draft_vs_sent(self):
        """Test that corresponding fieldsets are returned for drafts vs sent emails."""
        draft_email = EmailFactory(is_draft=True)
        sent_email = EmailFactory(is_draft=False)

        request = self._make_request("GET")

        # Draft should use "normal" fieldsets
        draft_fieldsets = self.admin.get_fieldsets(request, draft_email)
        self.assertEqual(draft_fieldsets, self.admin.fieldsets)

        # Sent email should use view-only fieldsets
        sent_fieldsets = self.admin.get_fieldsets(request, sent_email)
        self.assertEqual(sent_fieldsets, self.admin.view_fieldsets)

    def test_draft_creation_then_changing(self):
        """Test first creating draft then re-accessing and actually sending."""
        email = EmailFactory(
            subject="Test Draft Conversion to Sentianity",
            content="Draft content",
            recipients=[self.contact],
            # this will be set to True by response_add
            is_draft=False,
        )

        # Save as draft initially
        request = self._make_request("POST", data={"_save_draft": "Save Draft"})
        response = self.admin.response_add(request, email)

        email.refresh_from_db()
        self.assertTrue(email.is_draft)
        self.assertEqual(SendEmailTask.objects.count(), 0)

        # And now actually send it
        request = self._make_request("POST", data={"_save": "Send Email Now"})
        response = self.admin.response_change(request, email)

        # Check email is no longer a draft
        email.refresh_from_db()
        self.assertFalse(email.is_draft)

        # And that the email tasks are created and redirect happens properly
        self.assertGreater(SendEmailTask.objects.count(), 0)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/emails/sendemailtask", response.url)

    def test_draft_actions_display_for_drafts(self):
        """Test that the delete link is shown for draft emails, but not for others."""
        # Creating one draft and one sent to check the behaviour of each case.
        draft_email = EmailFactory(is_draft=True)
        sent_email = EmailFactory(is_draft=False)

        draft_actions = self.admin.draft_actions(draft_email)
        self.assertIn("deletelink", draft_actions)
        self.assertIn(f"/admin/emails/email/{draft_email.pk}/delete/", draft_actions)

        # For the sent email, only a "-" should be displayed
        sent_actions = self.admin.draft_actions(sent_email)
        self.assertEqual(sent_actions, "-")

    def test_delete_view_redirect(self):
        """
        Test that the delete view redirects to the emails list after successful deletion.
        """
        draft_email = EmailFactory(is_draft=True)

        request = self._make_request("GET")
        response = self.admin.delete_view(request, str(draft_email.pk))
        self.assertEqual(response.status_code, 200)

        request = self._make_request("POST", data={"post": "yes"})
        request._dont_enforce_csrf_checks = True
        response = self.admin.delete_view(request, str(draft_email.pk))

        # Should delete and redirect to changelist
        self.assertFalse(Email.objects.filter(pk=draft_email.pk).exists())
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/emails/email/", response.url)


class TestInvitationEmailAdminDrafts(TestCase):
    """Test draft functionality in InvitationEmailAdmin."""

    fixtures = [
        "initial/country",
        "initial/organizationtype",
        "initial/registrationrole",
    ]

    def setUp(self):
        self.site = AdminSite()
        self.admin = InvitationEmailAdmin(InvitationEmail, self.site)
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_superuser(
            email="drafty-admin@example.com", password="draft-password"
        )

        # Create test data
        self.org_type = OrganizationType.objects.first()
        self.organization = OrganizationFactory(organization_type=self.org_type)
        self.event = EventFactory()

    def _make_request(self, method, data=None):
        """HTTP requests helper; avoids too much boilerplate code."""
        if method == "POST":
            request = self.factory.post("/fake-url/", data or {})
        else:
            request = self.factory.get("/fake-url/")

        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_response_add_save_draft(self):
        """Test saving invitation email as draft."""
        email = InvitationEmailFactory(
            subject="Draft Invitation",
            content="Draft invitation content",
            events=[self.event],
            organization_types=[self.org_type],
            is_draft=False,
        )

        request = self._make_request("POST", data={"_save_draft": "Save Draft"})
        response = self.admin.response_add(request, email)

        # Check email is marked as draft
        email.refresh_from_db()
        self.assertTrue(email.is_draft)

        # Check redirect to changelist view and that no email tasks are created
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/emails/invitationemail", response.url)
        self.assertEqual(SendEmailTask.objects.count(), 0)

    def test_response_add_send_now(self):
        """Test sending invitation email immediately."""
        email = InvitationEmailFactory(
            subject="Send Invitation Now",
            content="Send invitation content",
            events=[self.event],
            organization_types=[self.org_type],
            is_draft=True,
        )

        request = self._make_request("POST", data={"_save": "Send Emails Now"})
        response = self.admin.response_add(request, email)

        # Check email is not a draft and redirect to tasks is happening
        email.refresh_from_db()
        self.assertFalse(email.is_draft)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/emails/sendemailtask", response.url)

    def test_response_post_save_add_draft_early_return(self):
        """Test that invitation drafts are not sent."""
        email = InvitationEmailFactory(
            subject="Draft Invitation",
            events=[self.event],
            organization_types=[self.org_type],
            is_draft=True,
        )

        request = self._make_request("POST")
        response = self.admin.response_post_save_add(request, email)

        # Should redirect to change view and no invitation task should be created
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/admin/emails/invitationemail/{email.pk}/change/", response.url)
        self.assertEqual(SendEmailTask.objects.count(), 0)

    def test_response_post_save_add_sent_invitation(self):
        """Test that sent invitations create tasks normally."""
        email = InvitationEmailFactory(
            subject="Sent Invitation",
            events=[self.event],
            organization_types=[self.org_type],
            is_draft=False,
        )

        request = self._make_request("POST")

        with patch("emails.services.get_organization_recipients") as mock_recipients:
            mock_recipients.return_value = {
                self.organization: {
                    "to_emails": ["test@example.com"],
                    "cc_emails": [],
                    "bcc_emails": [],
                    "to_contacts": [],
                    "cc_contacts": [],
                    "bcc_contacts": [],
                }
            }
            response = self.admin.response_post_save_add(request, email)

        self.assertGreater(SendEmailTask.objects.count(), 0)
        self.assertEqual(response.status_code, 302)

    def test_draft_permissions(self):
        """Test permissions differences between draft and sent emails."""
        draft_invitation = InvitationEmailFactory(is_draft=True)
        sent_invitation = InvitationEmailFactory(is_draft=False)

        request = self._make_request("GET")

        # Drafts should be editable and deletable
        self.assertTrue(self.admin.has_change_permission(request, draft_invitation))
        self.assertTrue(self.admin.has_delete_permission(request, draft_invitation))

        # Sent emails should not be editable or deletable
        self.assertFalse(self.admin.has_change_permission(request, sent_invitation))
        self.assertFalse(self.admin.has_delete_permission(request, sent_invitation))

    def test_draft_creation_then_changing(self):
        """Test first creating draft then re-accessing and actually sending."""
        email = InvitationEmailFactory(
            subject="Test Draft Conversion to Sentianity",
            events=[self.event],
            organization_types=[self.org_type],
            # this will be set to True by response_add
            is_draft=False,
        )

        # Save as draft initially
        request = self._make_request("POST", data={"_save_draft": "Save Draft"})
        response = self.admin.response_add(request, email)

        email.refresh_from_db()
        self.assertTrue(email.is_draft)
        self.assertEqual(SendEmailTask.objects.count(), 0)

        # NAnd then actually send it
        request = self._make_request("POST", data={"_save": "Send Email Now"})
        response = self.admin.response_change(request, email)

        # Check email is no longer a draft
        email.refresh_from_db()
        self.assertFalse(email.is_draft)

        # The email tasks should be created, and user redirected to them
        self.assertGreater(SendEmailTask.objects.count(), 0)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/emails/sendemailtask", response.url)

    def test_draft_actions_display_for_drafts(self):
        """Test that the delete link is shown for draft emails, but not for others."""
        # Creating one draft and one sent to check the behaviour of each case.
        draft_email = InvitationEmailFactory(is_draft=True)
        sent_email = InvitationEmailFactory(is_draft=False)

        draft_actions = self.admin.draft_actions(draft_email)
        self.assertIn("deletelink", draft_actions)
        self.assertIn(
            f"/admin/emails/invitationemail/{draft_email.pk}/delete/", draft_actions
        )

        # For the sent email, only a "-" should be displayed
        sent_actions = self.admin.draft_actions(sent_email)
        self.assertEqual(sent_actions, "-")

    def test_delete_view_redirect(self):
        """
        Test that the delete view redirects to the emails list after successful deletion.
        """
        draft_email = InvitationEmailFactory(is_draft=True)

        request = self._make_request("GET")
        response = self.admin.delete_view(request, str(draft_email.pk))
        self.assertEqual(response.status_code, 200)

        request = self._make_request("POST", data={"post": "yes"})
        request._dont_enforce_csrf_checks = True
        response = self.admin.delete_view(request, str(draft_email.pk))

        # Should delete and redirect to changelist
        self.assertFalse(InvitationEmail.objects.filter(pk=draft_email.pk).exists())
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/emails/invitationemail/", response.url)
