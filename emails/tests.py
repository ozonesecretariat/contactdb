from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from api.tests.factories import ContactFactory
from core.models import Contact, Country, Organization, OrganizationType
from emails.admin import InvitationEmailAdmin
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
            username="admin", email="admin@example.com", password="password"
        )

        # Create test data using fixture data
        self.org_type = OrganizationType.objects.first()
        self.organization = Organization.objects.create(
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
        invitation_email = InvitationEmailFactory(
            events=[self.event], organization_types=[self.org_type]
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user

        # Store messages
        request.session = "session"
        messages = []
        request._messages = messages

        response = self.admin.response_post_save_add(request, invitation_email)
        self.assertEqual(response.status_code, 200)

        # Verify tasks were created
        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 1)

        task = tasks.first()
        self.assertEqual(task.email, invitation_email)
        self.assertEqual(task.organization, self.organization)
        self.assertEqual(set(task.to_contacts.all()), {self.primary_contact})
        self.assertEqual(set(task.cc_contacts.all()), {self.secondary_contact})
        self.assertEqual(set(task.email_to), set(self.primary_contact.emails))

    def test_response_post_save_add_with_additional_contacts(self):
        """Test that additional CC/BCC contacts are included in tasks."""
        additional_cc = ContactFactory()
        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            cc_recipients=[additional_cc],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = "session"
        request._messages = []

        self.admin.response_post_save_add(request, invitation_email)

        task = SendEmailTask.objects.first()
        self.assertIn(additional_cc, task.cc_contacts.all())
