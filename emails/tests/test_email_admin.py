from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings

from api.tests.factories import (
    ContactFactory,
    OrganizationFactory,
)
from core.models import ContactGroup, Country, OrganizationType
from emails.admin import EmailAdmin
from emails.jobs import SendEmailJob
from emails.models import Email, SendEmailTask


@override_settings(RQ_QUEUES={"default": {"ASYNC": False}})
class TestEmailAdminOrganizations(TestCase):
    """Test organizations functionality in regular Email admin."""

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
            email="admin@example.com", password="password"
        )

        self.org_type = OrganizationType.objects.first()
        self.organization = OrganizationFactory(
            name="Test Org",
            organization_type=self.org_type,
            emails=["org@example.com"],
            email_ccs=["org-cc@example.com"],
            country=Country.objects.first(),
        )

        self.primary_contact = ContactFactory(
            first_name="Primary",
            last_name="Contact",
            organization=self.organization,
            emails=["primary@example.com"],
            email_ccs=["primary-cc@example.com"],
            country=self.organization.country,
        )

        self.secondary_contact = ContactFactory(
            first_name="Secondary",
            last_name="Contact",
            organization=self.organization,
            emails=["secondary@example.com"],
            email_ccs=["secondary-cc@example.com"],
            country=self.organization.country,
        )

        self.organization.primary_contacts.add(self.primary_contact)
        self.organization.secondary_contacts.add(self.secondary_contact)

    def test_email_with_organizations_creates_tasks(self):
        """Test that "normal" emails with organizations create tasks correctly."""

        org2 = OrganizationFactory(
            name="Joc Secund",
            organization_type=self.org_type,
        )

        primary2 = ContactFactory(
            first_name="Jane",
            last_name="Austen",
            organization=org2,
            emails=["jane@secondorg.com"],
            email_ccs=["jane-cc@secondorg.com"],
        )
        secondary2 = ContactFactory(
            first_name="Bob",
            last_name="Dylan",
            organization=org2,
            emails=["bob@secondorg.com"],
            email_ccs=["bob-cc@secondorg.com"],
        )
        org2.primary_contacts.add(primary2)
        org2.secondary_contacts.add(secondary2)

        email = Email.objects.create(
            subject="Test",
            content="Greeting, earth... organization members!",
            created_by=self.user,
        )
        email.organizations.add(self.organization)
        email.organizations.add(org2)

        # Simulate the response_post_save_add flow
        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        messages = FallbackStorage(request)
        request._messages = messages

        response = self.admin.response_post_save_add(request, email)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/emails/sendemailtask/", response.url)

        message_list = list(messages)
        self.assertEqual(len(message_list), 1)
        self.assertIn("emails scheduled for sending", str(message_list[0]))

        tasks = SendEmailTask.objects.filter(email=email)
        self.assertEqual(tasks.count(), 2)

        task_contacts = [task.contact for task in tasks]
        self.assertIn(self.primary_contact, task_contacts)
        self.assertIn(primary2, task_contacts)

        # Now actually try to mock sending the emails, then check the outbox
        for task in tasks:
            SendEmailJob.execute(None, task)
        self.assertEqual(len(mail.outbox), 2)

    def test_email_contacts_multiple_orgs(self):
        """Test contact computing for multiple organizations."""

        org2 = OrganizationFactory(
            name="Joc Secund",
            organization_type=self.org_type,
            emails=["org2@example.com"],
            email_ccs=["org2-cc@example.com"],
        )

        primary2 = ContactFactory(
            organization=org2,
            emails=["primary2@example.com"],
            email_ccs=["primary2-cc@example.com"],
        )
        secondary2 = ContactFactory(
            organization=org2,
            emails=["secondary2@example.com"],
            email_ccs=["secondary2-cc@example.com"],
        )
        org2.primary_contacts.add(primary2)
        org2.secondary_contacts.add(secondary2)

        email = Email.objects.create(
            subject="Test Multiple Organizations",
            content="Greetings, toutes les organizations!",
            created_by=self.user,
        )
        email.organizations.set([self.organization, org2])

        to_contacts = email.all_to_contacts
        self.assertIn(self.primary_contact, to_contacts)
        self.assertIn(primary2, to_contacts)
        self.assertNotIn(self.secondary_contact, to_contacts)
        self.assertNotIn(secondary2, to_contacts)

        cc_contacts = email.all_cc_contacts
        self.assertIn(self.secondary_contact, cc_contacts)
        self.assertIn(secondary2, cc_contacts)
        self.assertNotIn(self.primary_contact, cc_contacts)
        self.assertNotIn(primary2, cc_contacts)

    def test_regular_email_organizations_contacts(self):
        """Test that organization-based contacts are not duplicated on Email model."""

        shared_contact = ContactFactory(
            emails=["comunul@example.com"],
            email_ccs=["comunul-cc@example.com"],
        )
        self.organization.primary_contacts.add(shared_contact)

        email = Email.objects.create(
            subject="Test contacts duplication",
            content="Testing deduplication",
            created_by=self.user,
        )
        email.organizations.add(self.organization)
        email.recipients.add(shared_contact)

        # That shared contact should appear only once in all_to_contacts
        to_contacts = email.all_to_contacts
        contact_count = sum(1 for c in to_contacts if c == shared_contact)
        self.assertEqual(contact_count, 1)

        email.cc_recipients.add(shared_contact)
        self.organization.secondary_contacts.add(shared_contact)

        cc_contacts = email.all_cc_contacts
        contact_count = sum(1 for c in cc_contacts if c == shared_contact)
        self.assertEqual(contact_count, 1)

    def test_regular_email_mixed_recipients_deduplication(self):
        """
        Test contacts not duplicated across individual contacts, groups, organizations.
        """

        # Create a group with shared contact
        group = ContactGroup.objects.create(name="Test Group")
        group.contacts.add(self.primary_contact)

        email = Email.objects.create(
            subject="Test Mixed Recipients",
            content="Testing mixed recipient types",
            created_by=self.user,
        )

        # Add contact through multiple channels
        email.recipients.add(self.primary_contact)
        email.groups.add(group)
        email.organizations.add(self.organization)

        # Contact should appear only once despite multiple sources
        to_contacts = email.all_to_contacts
        contact_count = sum(1 for c in to_contacts if c == self.primary_contact)
        self.assertEqual(contact_count, 1)

    def test_regular_email_organizations_no_contacts(self):
        """Test organizations with no primary/secondary contacts."""

        empty_org = OrganizationFactory(
            name="Contactless Org",
            organization_type=self.org_type,
            emails=["contactless@example.com"],
        )

        email = Email.objects.create(
            subject="Test Contactless Organization",
            content="org with no contacts",
            created_by=self.user,
        )
        email.organizations.add(empty_org)

        to_contacts = email.all_to_contacts
        cc_contacts = email.all_cc_contacts

        self.assertEqual(len(to_contacts), 0)
        self.assertEqual(len(cc_contacts), 0)
