from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings

from api.tests.factories import ContactFactory, OrganizationFactory
from core.models import Contact, Country, OrganizationType
from emails.admin import InvitationEmailAdmin
from emails.jobs import SendEmailJob
from emails.models import InvitationEmail, SendEmailTask
from emails.tests.factories import InvitationEmailFactory
from events.models import Event


class TestInvitationEmailAdmin(TestCase):
    fixtures = [
        "initial/country",
        "initial/organizationtype",
        "initial/registrationstatus",
        "initial/registrationrole",
    ]

    def setUp(self):
        self.site = AdminSite()
        self.admin = InvitationEmailAdmin(InvitationEmail, self.site)
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="password"
        )

        # Create test data using fixture data
        self.org_type = OrganizationType.objects.first()
        self.organization = OrganizationFactory(
            name="Test Org",
            organization_type=self.org_type,
            emails=["org@example.com"],
            email_ccs=["org-cc@example.com"],
            country=Country.objects.first(),
        )

        self.event = Event.objects.create(
            code="TEST01",
            title="Test Event",
            start_date="2025-01-01",
            end_date="2025-01-02",
            venue_country=Country.objects.first(),
        )

        # Create contacts with emails
        self.primary_contact = Contact.objects.create(
            first_name="Primary",
            last_name="Contact",
            organization=self.organization,
            emails=["primary@example.com"],
            email_ccs=["primary-cc@example.com"],
            country=self.organization.country,
        )

        self.secondary_contact = Contact.objects.create(
            first_name="Secondary",
            last_name="Contact",
            organization=self.organization,
            emails=["secondary@example.com"],
            email_ccs=["secondary-cc@example.com"],
            country=self.organization.country,
        )

        # Set up organization contacts
        self.organization.primary_contacts.add(self.primary_contact)
        self.organization.secondary_contacts.add(self.secondary_contact)
        self.organization.save()

    def test_response_post_save_add_creates_tasks(self):
        """Test that email tasks are created for each organization."""
        self.organization.emails = ["org-main@example.com"]
        self.organization.email_ccs = ["org-cc@example.com"]
        self.organization.save()

        self.primary_contact.emails = ["primary-main@example.com"]
        self.primary_contact.email_ccs = ["primary-cc@example.com"]
        self.primary_contact.save()

        self.secondary_contact.emails = ["secondary-main@example.com"]
        self.secondary_contact.email_ccs = ["secondary-cc@example.com"]
        self.secondary_contact.save()
        invitation_email = InvitationEmailFactory(
            events=[self.event], organization_types=[self.org_type]
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        self.admin.response_post_save_add(request, invitation_email)

        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn("1 invitation emails scheduled for sending", str(messages[0]))

        # Verify tasks were created
        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 1)

        task = tasks.first()
        self.assertEqual(task.email, invitation_email)
        self.assertEqual(task.organization, self.organization)
        self.assertIsNotNone(task.invitation)
        self.assertEqual(task.invitation.event, self.event)
        self.assertEqual(task.invitation.organization, self.organization)

        self.assertEqual(set(task.to_contacts.all()), {self.primary_contact})
        expected_to_emails = {
            # organization email
            "org-main@example.com",
            # primary contact email
            "primary-main@example.com",
        }
        self.assertEqual(set(task.email_to), expected_to_emails)

        self.assertEqual(set(task.cc_contacts.all()), {self.secondary_contact})
        expected_cc_emails = {
            # organization.email_ccs
            "org-cc@example.com",
            # primary contact CC emails
            "primary-cc@example.com",
            # secondary contact main emails
            "secondary-main@example.com",
            # secondary contact CC emails
            "secondary-cc@example.com",
        }
        self.assertEqual(set(task.email_cc), expected_cc_emails)

    def test_response_post_save_add_with_additional_contacts(self):
        """Test that additional CC/BCC contacts are included in tasks."""
        additional_cc = ContactFactory(
            emails=["additional-main@example.com"],
            email_ccs=["additional-cc@example.com"],
        )
        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            cc_recipients=[additional_cc],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        self.admin.response_post_save_add(request, invitation_email)

        task = SendEmailTask.objects.first()
        self.assertIn(additional_cc, task.cc_contacts.all())

        self.assertIn("additional-main@example.com", task.email_cc)
        self.assertIn("additional-cc@example.com", task.email_cc)

    def test_response_post_save_add_with_multiple_organizations(self):
        """Test email task creation for multiple organizations."""
        # Create another organization with contacts
        org2 = OrganizationFactory(
            name="Second Org",
            organization_type=self.org_type,
            emails=["org2-main@example.com"],
            email_ccs=["org2-cc@example.com"],
            country=Country.objects.first(),
        )

        primary2 = ContactFactory(
            organization=org2,
            emails=["primary2-main@example.com"],
            email_ccs=["primary2-cc@example.com"],
        )
        org2.primary_contacts.add(primary2)

        invitation_email = InvitationEmailFactory(
            events=[self.event], organization_types=[self.org_type]
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        self.admin.response_post_save_add(request, invitation_email)

        # Should create one task per organization
        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 2)

        # Verify each task has the correct organizations set
        self.assertSetEqual({self.organization, org2}, {t.organization for t in tasks})

        # Verify each task has correct organization-specific emails
        for task in tasks:
            if task.organization == org2:
                self.assertIn("org2-main@example.com", task.email_to)
                self.assertIn("primary2-main@example.com", task.email_to)
                self.assertIn("org2-cc@example.com", task.email_cc)
                self.assertIn("primary2-cc@example.com", task.email_cc)
            else:
                self.assertNotIn("primary2-cc@example.com", task.email_cc)

    def test_response_post_save_add_additional_contacts_with_multiple_orgs(self):
        """Test that additional CC/BCC contacts are included in all tasks."""
        # Create another organization with contacts
        org2 = OrganizationFactory(
            name="Second Org",
            organization_type=self.org_type,
            emails=["org2-main@example.com"],
            email_ccs=["org2-cc@example.com"],
            country=Country.objects.first(),
        )

        primary2 = ContactFactory(
            organization=org2,
            emails=["primary2-main@example.com"],
            email_ccs=["primary2-cc@example.com"],
        )
        org2.primary_contacts.add(primary2)

        additional_cc = ContactFactory(
            emails=["additional-main@example.com"],
            email_ccs=["additional-cc@example.com"],
        )
        additional_bcc = ContactFactory(
            emails=["additional-bcc-main@example.com"],
            email_ccs=["additional-bcc@example.com"],
        )

        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            cc_recipients=[additional_cc],
            bcc_recipients=[additional_bcc],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        self.admin.response_post_save_add(request, invitation_email)

        # Should create one task per organization
        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 2)

        # Verify each task has the additional CCs and BCCs
        for task in tasks:
            self.assertIn("additional-main@example.com", task.email_cc)
            self.assertIn("additional-cc@example.com", task.email_cc)

            self.assertIn("additional-bcc-main@example.com", task.email_bcc)
            self.assertIn("additional-bcc@example.com", task.email_bcc)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_message_content(self):
        """Test that email messages are properly constructed and sent."""
        additional_cc = ContactFactory(
            emails=["cc@example.com"],
            email_ccs=["cc-secondary@example.com"],
        )
        additional_bcc = ContactFactory(
            emails=["additional-bcc-main@example.com"],
            email_ccs=["additional-bcc@example.com"],
        )
        invitation_email = InvitationEmailFactory(
            subject="Test Subject",
            content="Hello [[invitation_link]]",
            events=[self.event],
            organization_types=[self.org_type],
            cc_recipients=[additional_cc],
            bcc_recipients=[additional_bcc],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = "session"
        request._messages = FallbackStorage(request)

        # Clear the outbox
        mail.outbox = []

        # Trigger email sending
        self.admin.response_post_save_add(request, invitation_email)

        # Get the related task and execute it synchronously
        task = SendEmailTask.objects.first()
        SendEmailJob.execute(None, task)

        # Check that the email was sent & get it
        self.assertEqual(len(mail.outbox), 1)
        email_message = mail.outbox[0]

        # Verify email properties
        self.assertEqual(email_message.subject, "Test Subject")
        self.assertIn("Hello", email_message.body)
        self.assertIn("Hello", email_message.alternatives[0][0])
        self.assertEqual(email_message.from_email, settings.DEFAULT_FROM_EMAIL)

        # Verify recipients (must be the primary org mail and primary contact mail)
        self.assertSetEqual(
            set(email_message.to), {"org@example.com", "primary@example.com"}
        )
        self.assertSetEqual(
            set(email_message.cc),
            {
                "org-cc@example.com",
                "primary-cc@example.com",
                "secondary@example.com",
                "secondary-cc@example.com",
                "cc@example.com",
                "cc-secondary@example.com",
            },
        )
        self.assertSetEqual(
            set(email_message.bcc),
            {"additional-bcc@example.com", "additional-bcc-main@example.com"},
        )

        # Test HTML alternative
        html_content = email_message.alternatives[0][0]
        self.assertIn("text/html", email_message.alternatives[0][1])
        # TODO - test that the URL is being replaced
        self.assertNotIn("[[invitation_link]]", html_content)
        # self.assertIn(settings.MAIN_BACKEND_HOST, html_content)
        # TODO - add test for [[party]]
