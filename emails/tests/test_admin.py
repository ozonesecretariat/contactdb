from datetime import UTC, datetime, timedelta

from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from api.tests.factories import (
    ContactFactory,
    EventFactory,
    EventGroupFactory,
    EventInvitationFactory,
    OrganizationFactory,
    RegistrationFactory,
)
from common.urls import reverse
from core.models import Contact, Country, OrganizationType
from emails.admin import InvitationEmailAdmin
from emails.jobs import SendEmailJob
from emails.models import InvitationEmail, SendEmailTask
from emails.tests.factories import InvitationEmailFactory
from events.admin import EventAdmin
from events.models import Event


class TestInvitationEmailAdmin(TestCase):
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
            start_date=datetime(2025, 1, 1, tzinfo=UTC),
            end_date=datetime(2025, 1, 2, tzinfo=UTC),
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
        request.session = {}
        messages = FallbackStorage(request)
        request._messages = messages

        self.admin.response_post_save_add(request, invitation_email)

        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn("invitation emails scheduled for sending", str(messages[0]))

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
        request.session = {}
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
        request.session = {}
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
        request.session = {}
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

    def test_is_reminder_flag(self):
        """Test that the is_reminder flag is properly taken into account at save."""
        EventInvitationFactory(
            event=self.event,
            organization=self.organization,
        )
        original_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            is_reminder=False,
            subject="Original invitation to the intergalactic lawnmower convention",
        )
        reminder_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            is_reminder=True,
            original_email=original_email,
            subject="Urgent reminder for the intergalactic lawnmower convention",
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user

        request.session = {"reminder_original_email_id": original_email.id}
        messages = FallbackStorage(request)
        request._messages = messages

        self.admin.response_post_save_add(request, reminder_email)

        # Checking the correct message was displayed
        message_list = list(get_messages(request))
        self.assertEqual(len(message_list), 1)
        self.assertIn("reminder emails scheduled for sending", str(message_list[0]))

        # Checking the created tasks
        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 1)
        task = tasks.first()
        self.assertEqual(task.email, reminder_email)
        self.assertEqual(task.organization, self.organization)

        # Testing another reminder with the pre-existing invitation email created above
        reminder_email2 = InvitationEmailFactory(
            events=[self.event], organization_types=[self.org_type], is_reminder=True
        )

        request2 = self.factory.post("/fake-url/")
        request2.user = self.user
        request2.session = {"reminder_original_email_id": original_email.id}
        messages2 = FallbackStorage(request2)
        request2._messages = messages2

        self.admin.response_post_save_add(request2, reminder_email2)

        # Checking that reminder message is correctly displayed this time too
        message_list2 = list(get_messages(request2))
        self.assertEqual(len(message_list2), 1)
        self.assertIn("reminder emails scheduled for sending", str(message_list2[0]))

        # Aaand that reminder-related fields are properly set
        reminder_email2.refresh_from_db()
        self.assertEqual(reminder_email2.original_email, original_email)
        self.assertTrue(reminder_email2.is_reminder)

        # Verifying reminder flag persists even when reset (is_reminder=False)
        reminder_email3 = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            is_reminder=False,
        )

        request3 = self.factory.post("/fake-url/")
        request3.user = self.user
        request3.session = {"reminder_original_email_id": original_email.id}
        messages3 = FallbackStorage(request3)
        request3._messages = messages3

        self.admin.response_post_save_add(request3, reminder_email3)

        # Checking is_reminder is correctly set to True despite initially being False
        reminder_email3.refresh_from_db()
        self.assertTrue(InvitationEmail.objects.get(id=reminder_email3.id).is_reminder)
        self.assertEqual(reminder_email3.original_email, original_email)

        # Testing regular invitations (non-reminder) behaviour
        invitation_email = InvitationEmailFactory(
            events=[self.event], organization_types=[self.org_type], is_reminder=False
        )

        request4 = self.factory.post("/fake-url/")
        request4.user = self.user
        request4.session = {}
        messages4 = FallbackStorage(request4)
        request4._messages = messages4

        self.admin.response_post_save_add(request4, invitation_email)

        # Check that "normal" invitation (non-reminder) message is displayed
        message_list4 = list(get_messages(request4))
        self.assertEqual(len(message_list4), 1)
        self.assertIn("invitation emails scheduled for sending", str(message_list4[0]))
        self.assertNotIn("reminder emails scheduled for sending", str(message_list4[0]))

        # Aaand that reminder-related fields are not set
        invitation_email.refresh_from_db()
        self.assertFalse(invitation_email.is_reminder)
        self.assertIsNone(invitation_email.original_email)

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
        request.session = {}
        request._messages = FallbackStorage(request)

        # Clear the outbox
        mail.outbox = []

        # Trigger email sending
        self.admin.response_post_save_add(request, invitation_email)

        # Get the related task and execute it synchronously so we "send" the mail
        # (using the locmem.EmailBackend)
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

        # Verify recipients ("to" must be the primary org mails and primary contact mail)
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
        self.assertNotIn("[[invitation_link]]", html_content)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_invitation_email_placeholders(self):
        """Test placeholder expansion in invitation emails."""
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")

        # Create organization with contacts
        org = OrganizationFactory(
            name="Test Org",
            organization_type=gov_type,
            government=government,
            emails=["org@example.com"],
        )
        contact = ContactFactory(
            organization=org,
            first_name="John",
            last_name="Doe",
            title="Dr.",
            emails=["john@example.com"],
        )
        org.primary_contacts.add(contact)

        # Create invitation email with various placeholders:
        # [[party]] and [[invitation_link]] should expand, others should not.
        invitation_email = InvitationEmailFactory(
            subject="Invitation for [[party]]",
            content="""
                Dear [[first_name]] [[last_name]],

                Please add nominations at: [[invitation_link]]
                For: [[party]]

                Title: [[title]]
                Organization: [[organization]]
            """,
            events=[self.event],
            organization_types=[gov_type],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        mail.outbox = []
        self.admin.response_post_save_add(request, invitation_email)
        task = SendEmailTask.objects.first()
        # Need to explicitly execute the job non-async
        SendEmailJob.execute(None, task)

        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        email_message = mail.outbox[0]

        # Get the invitation that was created
        invitation = task.invitation

        # Check subject (party placeholder)
        self.assertEqual(email_message.subject, f"Invitation for {government.name}")

        # Contact-related placeholders should remain unchanged
        self.assertIn("Dear [[first_name]] [[last_name]]", email_message.body)
        self.assertIn("Title: [[title]]", email_message.body)
        self.assertIn("Organization: [[organization]]", email_message.body)

        # Invitation-related placeholders should be replaced
        self.assertIn(f"For: {government.name}", email_message.body)
        self.assertNotIn("[[invitation_link]]", email_message.body)
        self.assertIn(str(invitation.token), email_message.body)

        # Test cases with missing data
        org_no_gov = OrganizationFactory(
            organization_type=self.org_type,
            government=None,
            emails=["nogov@example.com"],
        )
        invitation_email_empty = InvitationEmailFactory(
            subject="Invitation for [[party]]",
            content="For: [[party]], Link: [[invitation_link]]",
            events=[self.event],
            organization_types=[self.org_type],
        )

        mail.outbox = []
        self.admin.response_post_save_add(request, invitation_email_empty)
        empty_fields_task = SendEmailTask.objects.get(organization=org_no_gov)
        SendEmailJob.execute(None, empty_fields_task)

        self.assertEqual(len(mail.outbox), 1)
        empty_fields_email = mail.outbox[0]
        empty_fields_invitation = empty_fields_task.invitation

        # Missing country should result in empty placeholder
        self.assertEqual(empty_fields_email.subject, "Invitation for ")
        self.assertIn("For: ,", empty_fields_email.body)

        # Link should still work even with missing country
        self.assertIn(str(empty_fields_invitation.token), empty_fields_email.body)


@override_settings(RQ_QUEUES={"default": {"ASYNC": False}})
class TestInvitationEmailAdminGovBehaviour(TestCase):
    """Test class for GOV-related behaviour in InvitationEmails."""

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
            email="admin@example.com", password="password"
        )

        self.org_type = OrganizationType.objects.first()
        self.event = Event.objects.create(
            code="TEST01",
            title="Test Event",
            start_date=datetime(2025, 1, 1, tzinfo=UTC),
            end_date=datetime(2025, 1, 2, tzinfo=UTC),
            venue_country=Country.objects.first(),
        )

    def test_response_post_save_add_with_gov_organization(self):
        """
        Test that inviting GOV organizations results in proper handling of
        all related organizations.
        """
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")

        # Create a GOV organization
        gov_org = OrganizationFactory(
            name="Government Org",
            organization_type=gov_type,
            government=government,
            emails=["gov@example.com"],
            email_ccs=["gov-cc@example.com"],
        )

        # Create related organizations in same country
        related_org1 = OrganizationFactory(
            name="Related Org 1",
            organization_type=self.org_type,
            government=government,
            emails=["related1@example.com"],
            email_ccs=["related1-cc@example.com"],
        )
        related_org2 = OrganizationFactory(
            name="Related Org 2",
            organization_type=self.org_type,
            government=government,
            emails=["related2@example.com"],
            email_ccs=["related2-cc@example.com"],
        )

        # Add contacts to organizations
        gov_contact = ContactFactory(
            organization=gov_org,
            emails=["gov-contact@example.com"],
            email_ccs=["gov-contact-cc@example.com"],
        )
        related_contact1 = ContactFactory(
            organization=related_org1,
            emails=["related1-contact@example.com"],
            email_ccs=["related1-contact-cc@example.com"],
        )
        related_contact2 = ContactFactory(
            organization=related_org2,
            emails=["related2-contact@example.com"],
            email_ccs=["related2-contact-cc@example.com"],
        )

        gov_org.primary_contacts.add(gov_contact)
        related_org1.primary_contacts.add(related_contact1)
        related_org2.primary_contacts.add(related_contact2)

        # Create invitation email
        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[gov_type],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, invitation_email)

        # Get created tasks
        tasks = SendEmailTask.objects.all()

        # Should only create one task for the GOV org
        self.assertEqual(tasks.count(), 1)

        task = tasks.first()
        self.assertEqual(task.organization, gov_org)

        # Check that invitation is linked to country, not organization
        self.assertEqual(task.invitation.country, government)
        self.assertIsNone(task.invitation.organization)

        # Verify all related org emails are included
        expected_to_emails = {
            "gov@example.com",
            "related1@example.com",
            "related2@example.com",
            "gov-contact@example.com",
            "related1-contact@example.com",
            "related2-contact@example.com",
        }
        self.assertEqual(set(task.email_to), expected_to_emails)

        expected_cc_emails = {
            "gov-cc@example.com",
            "related1-cc@example.com",
            "related2-cc@example.com",
            "gov-contact-cc@example.com",
            "related1-contact-cc@example.com",
            "related2-contact-cc@example.com",
        }
        self.assertEqual(set(task.email_cc), expected_cc_emails)

    def test_response_post_save_add_with_countryless_gov_organization(self):
        """
        Test that inviting both "normal" and countryless GOV organizations results in
        proper handling of all related organizations.
        """
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")

        # Create a GOV organization
        gov_org = OrganizationFactory(
            name="Government Org",
            organization_type=gov_type,
            government=government,
        )

        # Create related organizations in same country
        related_org1 = OrganizationFactory(
            name="Related Org 1",
            organization_type=self.org_type,
            government=government,
        )
        related_org2 = OrganizationFactory(
            name="Related Org 2",
            organization_type=self.org_type,
            government=government,
        )

        # Create a GOV organization with no country
        countryless_gov_org = OrganizationFactory(
            name="Countryless Government Org",
            organization_type=gov_type,
            government=None,
        )

        # Add contacts to organizations
        gov_contact = ContactFactory(
            organization=gov_org,
        )
        related_contact1 = ContactFactory(organization=related_org1)
        related_contact2 = ContactFactory(organization=related_org2)

        gov_org.primary_contacts.add(gov_contact)
        related_org1.primary_contacts.add(related_contact1)
        related_org2.primary_contacts.add(related_contact2)

        # Create invitation email
        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[gov_type],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, invitation_email)

        # Get created tasks
        tasks = SendEmailTask.objects.all()

        # Should create 2 tasks - one for countryless GOV, other for all others
        self.assertEqual(tasks.count(), 2)

        # Check country-linked invitation
        task = tasks.filter(invitation__country__isnull=False).first()
        self.assertIsNotNone(task)
        self.assertEqual(task.organization, gov_org)
        self.assertEqual(task.invitation.country, government)
        self.assertIsNone(task.invitation.organization)

        # Check organization-linked invitation
        task = tasks.filter(invitation__country__isnull=True).first()
        self.assertIsNotNone(task)
        self.assertIsNotNone(task.invitation.organization)
        self.assertEqual(task.organization, countryless_gov_org)
        self.assertIsNone(task.invitation.country)

    def test_response_post_save_add_with_gov_and_regular_orgs(self):
        """
        Test that invitations are correctly created for GOV and regular orgs,
        from the same country.
        """
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")

        # Create a GOV organization and its contacts
        gov_org = OrganizationFactory(
            name="Government Org",
            organization_type=gov_type,
            government=government,
            emails=["gov@example.com"],
        )
        gov_contact = ContactFactory(
            organization=gov_org,
            emails=["gov-contact@example.com"],
        )
        gov_org.primary_contacts.add(gov_contact)

        # Create related org (same country as GOV)
        related_org = OrganizationFactory(
            name="Related Org",
            organization_type=self.org_type,
            government=government,
            emails=["related@example.com"],
        )
        related_contact = ContactFactory(
            organization=related_org,
            emails=["related-contact@example.com"],
        )
        related_org.primary_contacts.add(related_contact)

        # Create unrelated org (no government)
        unrelated_org = OrganizationFactory(
            name="Unrelated Org",
            organization_type=self.org_type,
            government=None,
            emails=["unrelated@example.com"],
        )
        unrelated_contact = ContactFactory(
            organization=unrelated_org,
            emails=["unrelated-contact@example.com"],
        )
        unrelated_org.primary_contacts.add(unrelated_contact)

        # Create invitation email with both types
        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[gov_type, self.org_type],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, invitation_email)

        # Check created tasks
        tasks = SendEmailTask.objects.all()

        # Should create 2 tasks - one for GOV (including related) and one for unrelated
        self.assertEqual(tasks.count(), 2)

        # Check GOV task
        gov_task = tasks.get(organization=gov_org)
        self.assertEqual(gov_task.invitation.country, government)
        self.assertIsNone(gov_task.invitation.organization)

        # GOV task should include related org emails
        expected_gov_emails = {
            "gov@example.com",
            "gov-contact@example.com",
            "related@example.com",
            "related-contact@example.com",
        }
        self.assertEqual(set(gov_task.email_to), expected_gov_emails)

        # Check unrelated org task
        unrelated_task = tasks.get(organization=unrelated_org)
        self.assertIsNone(unrelated_task.invitation.country)
        self.assertEqual(unrelated_task.invitation.organization, unrelated_org)

        # Unrelated task should only have its own email addresses
        expected_unrelated_emails = {
            "unrelated@example.com",
            "unrelated-contact@example.com",
        }
        self.assertEqual(set(unrelated_task.email_to), expected_unrelated_emails)

        # No task was created for the related org
        self.assertFalse(
            tasks.filter(organization=related_org).exists(),
            "Should not create separate task for org related to GOV",
        )

    def test_response_post_save_add_with_mixed_organizations(self):
        """Test handling of GOV and non-GOV orgs from different countries."""
        # Create two governments
        government1 = Country.objects.first()
        government2 = Country.objects.create(code="XX", name="Test Country")

        gov_type = OrganizationType.objects.get(acronym="GOV")

        # GOV orgs
        gov_org1 = OrganizationFactory(
            organization_type=gov_type,
            government=government1,
            emails=["gov1@example.com"],
        )
        OrganizationFactory(
            organization_type=gov_type,
            government=government2,
            emails=["gov2@example.com"],
            email_ccs=["gov2-cc@example.org"],
        )
        # Related org
        OrganizationFactory(
            organization_type=self.org_type,
            government=government1,
            emails=["related1@example.com"],
        )
        unrelated_org = OrganizationFactory(
            organization_type=self.org_type,
            government=None,
            emails=["unrelated@example.com"],
        )

        # Create invitation email
        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[gov_type, self.org_type],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, invitation_email)

        tasks = SendEmailTask.objects.all()

        # Should create 3 tasks: 2 for GOV orgs (different countries) and 1 for unrelated org
        self.assertEqual(tasks.count(), 3)

        # Check GOV tasks have country-based invitations
        gov_tasks = tasks.filter(organization__organization_type=gov_type)
        self.assertEqual(gov_tasks.count(), 2)

        for task in gov_tasks:
            self.assertEqual(task.invitation.country, task.organization.government)
            if task.organization == gov_org1:
                self.assertIn("related1@example.com", task.email_to)

        # Check unrelated org has its own invitation
        unrelated_task = tasks.get(organization=unrelated_org)
        self.assertIsNone(unrelated_task.invitation.country)
        self.assertEqual(unrelated_task.invitation.organization, unrelated_org)

    def test_response_post_save_add_multiple_gov_organizations(self):
        """Test handling of multiple GOV organizations from same country."""
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")

        # GOV orgs
        gov_org1 = OrganizationFactory(
            organization_type=gov_type,
            government=government,
            emails=["gov1@example.com"],
        )
        OrganizationFactory(
            organization_type=gov_type,
            government=government,
            emails=["gov2@example.com"],
            email_ccs=["gov2-cc@example.org"],
        )
        # Related org
        OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            emails=["related1@example.com"],
        )
        unrelated_org = OrganizationFactory(
            organization_type=self.org_type,
            government=None,
            emails=["unrelated@example.com"],
        )

        additional_cc = ContactFactory(
            emails=["additional-main@example.com"],
            email_ccs=["additional-cc@example.com"],
        )
        additional_bcc = ContactFactory(
            emails=["additional-bcc@example.com"],
            email_ccs=["additional-bcc@example.com"],
        )

        # Create invitation email
        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[gov_type, self.org_type],
            cc_recipients=[additional_cc],
            bcc_recipients=[additional_bcc],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, invitation_email)

        tasks = SendEmailTask.objects.all()

        # Should create 2 tasks: 1 for GOV & related orgs and 1 for unrelated org
        self.assertEqual(tasks.count(), 2)

        # Check GOV tasks have country-based invitations
        gov_tasks = tasks.filter(organization__organization_type=gov_type)
        self.assertEqual(gov_tasks.count(), 1)

        task = gov_tasks.first()

        # Check that government is set correctly
        self.assertEqual(task.invitation.country, task.organization.government)
        self.assertEqual(gov_org1.government, task.organization.government)

        # Check that (B)CC's are not duplicated and all contacts are included
        self.assertEqual(len(task.email_cc), len(set(task.email_cc)))
        self.assertEqual(len(task.email_bcc), len(set(task.email_bcc)))
        self.assertSetEqual(
            set(task.email_to),
            {"gov1@example.com", "gov2@example.com", "related1@example.com"},
        )

        # Check unrelated org has its own invitation
        unrelated_task = tasks.get(organization=unrelated_org)
        self.assertIsNone(unrelated_task.invitation.country)
        self.assertEqual(unrelated_task.invitation.organization, unrelated_org)

    def test_response_post_save_add_no_gov_involved(self):
        """Test that everything works OK when there is no GOV invitation"""
        government = Country.objects.first()
        OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            emails=["related1@example.com"],
        )
        OrganizationFactory(
            organization_type=self.org_type,
            government=None,
            emails=["unrelated@example.com"],
        )

        # Create invitation email
        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, invitation_email)

        tasks = SendEmailTask.objects.all()

        # Should create 2 tasks for each organization
        self.assertEqual(tasks.count(), 2)

    def test_response_post_save_add_with_organizations_list(self):
        """Test that specific organizations are used when provided."""
        # Create multiple orgs, but only specify some in the list
        org1 = OrganizationFactory(
            organization_type=self.org_type, emails=["org1@example.com"]
        )
        org2 = OrganizationFactory(
            organization_type=self.org_type, emails=["org2@example.com"]
        )
        org3 = OrganizationFactory(
            organization_type=self.org_type, emails=["org3@example.com"]
        )

        # Add contacts
        ContactFactory(organization=org1, emails=["contact1@example.com"])
        ContactFactory(organization=org2, emails=["contact2@example.com"])
        ContactFactory(organization=org3, emails=["contact3@example.com"])

        # Create invitation email only for org1 and org2
        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organizations=[org1, org2],
            organization_types=[],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, invitation_email)

        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 2)

        task_orgs = {task.organization for task in tasks}
        self.assertEqual(task_orgs, {org1, org2})
        # There should be not task for org3
        self.assertNotIn(org3, task_orgs)

    def test_specific_organizations_with_include_in_invitation_flag(self):
        """
        Test that organizations in list are included even when
        include_in_invitation=False.
        """
        org_not_included = OrganizationFactory(
            organization_type=self.org_type,
            include_in_invitation=False,
            emails=["not-included@example.com"],
        )
        org_included = OrganizationFactory(
            organization_type=self.org_type,
            include_in_invitation=True,
            emails=["included@example.com"],
        )

        ContactFactory(organization=org_not_included, emails=["contact1@example.com"])
        ContactFactory(organization=org_included, emails=["contact2@example.com"])

        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organizations=[org_not_included, org_included],
            organization_types=[],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, invitation_email)

        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 2)

        # Both orgs should have tasks, regardless of include_in_invitation flag
        task_orgs = {task.organization for task in tasks}
        self.assertEqual(task_orgs, {org_not_included, org_included})

    def test_organizations_list_gov_expands_include_true(self):
        """
        Test that GOV orgs in specified orgs list "expands" (adds related orgs contacts)
        if GOV org's include_in_invitation is True.
        """
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")

        gov_org = OrganizationFactory(
            organization_type=gov_type,
            government=government,
            include_in_invitation=True,
            emails=["gov@example.com"],
        )
        related_org = OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
            emails=["related@example.com"],
        )

        gov_contact = ContactFactory(
            organization=gov_org, emails=["gov-contact@example.com"]
        )
        related_contact = ContactFactory(
            organization=related_org, emails=["related-contact@example.com"]
        )
        gov_org.primary_contacts.add(gov_contact)
        related_org.primary_contacts.add(related_contact)

        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organizations=[gov_org],
            organization_types=[],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, invitation_email)

        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 1)

        task = tasks.first()
        self.assertEqual(task.organization, gov_org)

        # Should include related org emails
        expected_emails = {
            "gov@example.com",
            "gov-contact@example.com",
            "related@example.com",
            "related-contact@example.com",
        }
        self.assertEqual(set(task.email_to), expected_emails)

    def test_organizations_list_gov_expands_include_false(self):
        """
        Test that GOV orgs in specified orgs list "expands" (adds related orgs contacts)
        if GOV org's include_in_invitation is False.
        """
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")

        gov_org = OrganizationFactory(
            organization_type=gov_type,
            government=government,
            include_in_invitation=False,
            emails=["gov@example.com"],
        )
        related_org = OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
            emails=["related@example.com"],
        )

        gov_contact = ContactFactory(
            organization=gov_org, emails=["gov-contact@example.com"]
        )
        related_contact = ContactFactory(
            organization=related_org, emails=["related-contact@example.com"]
        )
        gov_org.primary_contacts.add(gov_contact)
        related_org.primary_contacts.add(related_contact)

        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organizations=[gov_org],
            organization_types=[],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, invitation_email)

        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 1)

        task = tasks.first()
        self.assertEqual(task.organization, gov_org)

        # Should include related org emails
        expected_emails = {
            "gov@example.com",
            "gov-contact@example.com",
            "related@example.com",
            "related-contact@example.com",
        }
        self.assertEqual(set(task.email_to), expected_emails)

    def test_email_duplication(self):
        """Test that emails are not duplicated across to, cc and bcc."""
        # Create organization with overlapping emails
        org = OrganizationFactory(
            name="My duplication clone",
            organization_type=self.org_type,
            emails=["main@example.com", "overlap@example.com"],
            email_ccs=["cc@example.com", "overlap@example.com"],
        )

        # Primary contact with emails that overlap with org & additional cc
        primary_contact = ContactFactory(
            organization=org,
            # Duplicate with org added below
            emails=["primary@example.com", "overlap@example.com"],
            email_ccs=[
                "primary-cc@example.com",
                # Duplicate with org CC added below
                "cc@example.com",
            ],
        )
        org.primary_contacts.add(primary_contact)

        # Secondary contact with emails overlapping all categories
        secondary_contact = ContactFactory(
            organization=org,
            # Duplicate with primary added below
            emails=["secondary@example.com", "primary@example.com"],
            # Duplicate with one of org's "to" emails added below
            email_ccs=["secondary-cc@example.com", "main@example.com"],
        )
        org.secondary_contacts.add(secondary_contact)

        # Additional CC recipient with overlapping emails
        additional_cc = ContactFactory(
            # Duplicate with one of org's primary contact's to emails added below
            emails=["additional@example.com", "overlap@example.com"],
            # Duplicate with one of org's primary cc emails added below
            email_ccs=["additional-cc@example.com", "primary-cc@example.com"],
        )

        # Additional BCC recipient with emails overlapping all other categories
        additional_bcc = ContactFactory(
            # Duplicate with org main added below
            emails=["bcc@example.com", "main@example.com"],
            email_ccs=[
                "bcc-cc@example.com",
                # Duplicate with primary main added below
                "primary@example.com",
            ],
        )

        # Create and send email
        invitation_email = InvitationEmailFactory(
            subject="Am I a clone or am I a duplicate?",
            content="Testing email duplication scenarios",
            events=[self.event],
            organization_types=[self.org_type],
            cc_recipients=[additional_cc],
            bcc_recipients=[additional_bcc],
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        mail.outbox = []
        self.admin.response_post_save_add(request, invitation_email)
        self.assertEqual(SendEmailTask.objects.count(), 1)
        task = SendEmailTask.objects.first()

        # Composing sets from the task to use below
        task_to_emails = set(task.email_to)
        task_cc_emails = set(task.email_cc)
        task_bcc_emails = set(task.email_bcc)

        # Checking no contact duploicates inside each "category" (to, cc, bcc)
        self.assertEqual(len(task.email_to), len(task_to_emails))
        self.assertEqual(len(task.email_cc), len(task_cc_emails))
        self.assertEqual(len(task.email_bcc), len(task_bcc_emails))

        # Checking there's no contact overlap between categories in the task
        self.assertEqual(len(task_to_emails.intersection(task_cc_emails)), 0)
        self.assertEqual(len(task_to_emails.intersection(task_bcc_emails)), 0)
        self.assertEqual(len(task_cc_emails.intersection(task_bcc_emails)), 0)

        # Execute the job and check the actual email
        SendEmailJob.execute(None, task)
        self.assertEqual(len(mail.outbox), 1)
        email_message = mail.outbox[0]

        # Composing the email sets ahead of time to use in comparisons below
        to_emails = set(email_message.to)
        cc_emails = set(email_message.cc)
        bcc_emails = set(email_message.bcc)

        # Check there's no email duplicates within each category
        self.assertEqual(len(email_message.to), len(to_emails))
        self.assertEqual(len(email_message.cc), len(cc_emails))
        self.assertEqual(len(email_message.bcc), len(bcc_emails))

        # Check there's no email overlap between categories
        self.assertEqual(len(to_emails.intersection(cc_emails)), 0)
        self.assertEqual(len(to_emails.intersection(bcc_emails)), 0)
        self.assertEqual(len(cc_emails.intersection(bcc_emails)), 0)

        expected_to = {"main@example.com", "overlap@example.com", "primary@example.com"}
        self.assertSetEqual(expected_to, to_emails)

        self.assertSetEqual(expected_to.intersection(cc_emails), set())
        self.assertSetEqual(expected_to.intersection(bcc_emails), set())

        expected_cc = {
            "cc@example.com",
            "primary-cc@example.com",
            "secondary@example.com",
            "secondary-cc@example.com",
            "additional@example.com",
            "additional-cc@example.com",
        }
        self.assertSetEqual(expected_cc, cc_emails)

        self.assertSetEqual(expected_cc.intersection(bcc_emails), set())
        expected_bcc = {"bcc@example.com", "bcc-cc@example.com"}
        self.assertSetEqual(expected_bcc, bcc_emails)

        # No unexpected emails should appear in neither "category"
        all_expected = expected_to | expected_cc | expected_bcc
        all_actual = to_emails | cc_emails | bcc_emails
        self.assertSetEqual(
            all_actual - all_expected,
            set(),
        )


@override_settings(RQ_QUEUES={"default": {"ASYNC": False}})
class TestInvitationEmailAdminReminders(TestCase):
    """Test reminder functionality in InvitationEmailAdmin."""

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
            email="admin@example.com", password="password"
        )

        self.org_type = OrganizationType.objects.first()
        self.organization = OrganizationFactory(organization_type=self.org_type)
        self.event = EventFactory()

    def test_send_reminder_view_single_email(self):
        """Test sending reminder starting from a single invitation email."""
        # Create original invitation email
        original_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            is_reminder=False,
        )

        request = self.factory.get(f"/fake-url/{original_email.id}/send-reminder/")
        request.user = self.user
        request.session = {}
        messages = FallbackStorage(request)
        request._messages = messages

        response = self.admin.send_reminder_view(request, original_email.id)

        # Should redirect to add page with proper parameters
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/emails/invitationemail/add/", response.url)
        self.assertIn("is_reminder=1", response.url)
        self.assertIn(f"original_email_id={original_email.id}", response.url)

    def test_add_view_with_reminder_parameters(self):
        """Test the pre-population of fields when creating reminders."""
        # Create original email and invitation
        original_email = InvitationEmailFactory(
            subject="Original Subject",
            content="Original content",
            events=[self.event],
            organization_types=[self.org_type],
        )

        # Create invitation so we can test unregistered orgs
        EventInvitationFactory(
            event=self.event,
            organization=self.organization,
        )

        request = self.factory.get(
            f"/fake-url/add/?is_reminder=1&original_email_id={original_email.id}"
        )
        request.user = self.user
        request.session = {}

        response = self.admin.add_view(request)
        self.assertEqual(response.status_code, 200)

        context = response.context_data
        adminform = context["adminform"]
        form = adminform.form

        self.assertEqual(form.initial["events"], [self.event.pk])
        self.assertEqual(form.initial["original_email"], original_email.pk)
        self.assertEqual(form.initial["subject"], "Reminder: Original Subject")
        self.assertEqual(form.initial.get("content"), "Original content")
        self.assertTrue(form.initial["is_reminder"])
        self.assertIn(self.org_type.pk, form.initial["organization_types"])

        # Check session data is set
        self.assertEqual(
            request.session["reminder_original_email_id"], str(original_email.id)
        )

    def test_original_email_link_display(self):
        """Test the original_email_link display method."""
        original_email = InvitationEmailFactory(subject="Original")
        reminder_email = InvitationEmailFactory(
            is_reminder=True, original_email=original_email
        )

        html = self.admin.original_email_link(reminder_email)
        self.assertIn(original_email.subject, html)
        self.assertIn(
            reverse("admin:emails_invitationemail_change", args=[original_email.id]),
            html,
        )

    def test_reminder_count_display(self):
        """Test that the reminder count is properly displayed."""
        original_email = InvitationEmailFactory()

        # No reminders initially
        self.assertEqual(self.admin.reminder_count(original_email), "0")

        # Add reminders
        InvitationEmailFactory(is_reminder=True, original_email=original_email)
        InvitationEmailFactory(is_reminder=True, original_email=original_email)

        html = self.admin.reminder_count(original_email)
        self.assertIn("2 reminders", html)
        self.assertIn(f"original_email__id__exact={original_email.pk}", html)

    def test_change_view_reminder_button(self):
        """Test that reminder button appears in detail view for invitations."""
        original_email = InvitationEmailFactory(is_reminder=False)

        request = self.factory.get(f"/fake-url/{original_email.id}/change/")
        request.user = self.user

        response = self.admin.change_view(request, str(original_email.id))

        # Should show reminder button
        self.assertTrue(response.context_data["show_reminder_button"])
        self.assertIn("send-reminder", response.context_data["reminder_url"])

    def test_change_view_reminder_button_for_reminders(self):
        """Test that reminder button does not appear for reminder emails."""
        original_email = InvitationEmailFactory(
            subject="Original Email",
            is_reminder=False,
            original_email=None,
        )
        reminder_email = InvitationEmailFactory(
            subject="Reminder Email",
            is_reminder=True,
            original_email=original_email,
        )

        request = self.factory.get(f"/fake-url/{reminder_email.id}/change/")
        request.user = self.user
        response = self.admin.change_view(request, str(original_email.id))

        self.assertTrue(response.context_data["show_reminder_button"])
        self.assertIn("send-reminder", response.context_data["reminder_url"])

        request = self.factory.get(f"/fake-url/{reminder_email.id}/change/")
        request.user = self.user
        response = self.admin.change_view(request, str(reminder_email.id))

        self.assertTrue(response.context_data["show_reminder_button"])
        self.assertIn("send-reminder", response.context_data["reminder_url"])
        self.assertEqual(response.context_data["original_email"], original_email)

    def test_reminder_includes_all_country_organizations(self):
        """
        Test that reminders for country-level invitations include *all* organizations
        from that country, not just GOV organizations.
        """

        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")

        # Create GOV organization
        gov_org = OrganizationFactory(
            name="GOV Org",
            organization_type=gov_type,
            government=government,
            include_in_invitation=True,
            emails=["gov@example.com"],
        )
        gov_contact = ContactFactory(
            organization=gov_org, emails=["gov-contact@example.com"]
        )
        gov_org.primary_contacts.add(gov_contact)

        # Create a non-GOV organization that has the same government
        non_gov_org = OrganizationFactory(
            name="Non-GOV Org",
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
            emails=["nongov@example.com"],
        )
        non_gov_contact = ContactFactory(
            organization=non_gov_org, emails=["nongov-contact@example.com"]
        )
        non_gov_org.primary_contacts.add(non_gov_contact)

        EventInvitationFactory(
            event=self.event,
            country=government,
            organization=None,
        )
        EventInvitationFactory(
            event=self.event,
            organization=non_gov_org,
            country=None,
        )

        # Only registering the GOV org
        RegistrationFactory(
            event=self.event,
            contact=gov_contact,
        )

        # Create initial invitation email for all organizations
        original_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[gov_type, self.org_type],
            subject="Original Invitation",
        )

        unregistered_orgs = list(original_email.unregistered_organizations)

        # Checking that only registered orgs are included
        self.assertIn(non_gov_org, unregistered_orgs)
        self.assertNotIn(gov_org, unregistered_orgs)

        # Test reminder creation
        reminder_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[gov_type, self.org_type],
            is_reminder=True,
            subject="Reminder Email",
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {"reminder_original_email_id": str(original_email.id)}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, reminder_email)

        # Check reminder is only sent to unregistered organizations
        tasks = SendEmailTask.objects.all()

        non_gov_task = tasks.filter(organization=non_gov_org).first()
        self.assertIsNotNone(non_gov_task)
        gov_task = tasks.filter(organization=gov_org).first()
        self.assertIsNone(gov_task)
        self.assertEqual(tasks.count(), 1)

    def test_reminder_respects_include_in_invitation_flag(self):
        """Test that only organizations with include_in_invitation=True are included."""
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")

        # Create organization with include_in_invitation=False
        excluded_org = OrganizationFactory(
            name="Excluded Org",
            organization_type=self.org_type,
            government=government,
            include_in_invitation=False,
        )
        # Aaand one as well with the flag set to True
        included_org = OrganizationFactory(
            name="Included Org",
            organization_type=gov_type,
            government=government,
            include_in_invitation=True,
        )
        ContactFactory(organization=included_org)

        # Create country-level invitation
        EventInvitationFactory(
            event=self.event,
            country=government,
            organization=None,
        )

        # Create original invitation email
        original_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[gov_type],
        )

        # Test that non-include-in-invitation org is not in unregistered_organizations
        unregistered_orgs = list(original_email.unregistered_organizations)
        self.assertNotIn(excluded_org, unregistered_orgs)
        self.assertIn(included_org, unregistered_orgs)

    def test_reminder_multiple_invitation_emails(self):
        """
        Test that only the orgs with the invitation email org types receive a reminder
        when there are multiple invitation emails (with mutually-exclusive org types)
        """
        government = Country.objects.first()
        ass_panel_type = OrganizationType.objects.get(acronym="ASS-PANEL")

        # Create organizations for each invitation email to be sent
        first_email_org_1 = OrganizationFactory(
            name="Excluded Org",
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
        )
        first_email_org_2 = OrganizationFactory(
            name="Excluded Org",
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
        )
        second_email_org = OrganizationFactory(
            name="Included Org",
            organization_type=ass_panel_type,
            government=None,
            include_in_invitation=True,
        )
        ContactFactory(organization=first_email_org_1)
        ContactFactory(organization=first_email_org_2)
        ContactFactory(organization=second_email_org)

        # Create invitations for all orgs
        EventInvitationFactory(
            event=self.event,
            country=None,
            organization=first_email_org_1,
        )
        # This should actually invite first_email_org_2
        EventInvitationFactory(
            event=self.event,
            country=government,
            organization=None,
        )
        EventInvitationFactory(
            event=self.event,
            country=None,
            organization=second_email_org,
        )

        # Create invitation email for first_email_org_1/2
        first_invitation_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
        )
        # And one invitation email for second_email_org
        second_invitation_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[ass_panel_type],
        )

        # Test that organizations are present in unregistered_organizations based on
        # the appropriate original invitation email.
        unregistered_orgs_1 = list(first_invitation_email.unregistered_organizations)
        self.assertIn(first_email_org_1, unregistered_orgs_1)
        self.assertIn(first_email_org_2, unregistered_orgs_1)
        self.assertNotIn(second_email_org, unregistered_orgs_1)

        unregistered_orgs_2 = list(second_invitation_email.unregistered_organizations)
        self.assertNotIn(first_email_org_1, unregistered_orgs_2)
        self.assertNotIn(first_email_org_2, unregistered_orgs_2)
        self.assertIn(second_email_org, unregistered_orgs_2)

    def test_reminder_with_no_unregistered_organizations(self):
        """Test reminder creation when all organizations have registered."""
        government = Country.objects.first()
        org = OrganizationFactory(
            name="The Crystal Globe global readers",
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
        )
        contact = ContactFactory(organization=org)

        # Register the organization
        RegistrationFactory(event=self.event, contact=contact)

        original_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
        )

        unregistered_orgs = list(original_email.unregistered_organizations)
        self.assertNotIn(org, unregistered_orgs)

        # Test reminder creation does not fail, but sends no emails
        reminder_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            is_reminder=True,
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {"reminder_original_email_id": str(original_email.id)}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, reminder_email)

        # No tasks should be created, however success message is displayed
        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 0)
        messages_list = list(get_messages(request))
        self.assertEqual(len(messages_list), 1)
        self.assertIn("reminder emails scheduled", str(messages_list[0]))

    def test_reminder_with_event_group(self):
        """Test reminder work as well with event groups."""
        event_group = EventGroupFactory(name="Multi-Day Conference")
        event1 = EventFactory(title="Day 1")
        event2 = EventFactory(title="Day 2")
        event_group.events.add(event1, event2)

        government = Country.objects.first()
        org = OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
        )

        # Create invitation & email for event group rather than event
        EventInvitationFactory(
            event=None,
            event_group=event_group,
            organization=None,
            country=government,
        )

        original_email = InvitationEmailFactory(
            events=[],
            event_group=event_group,
            organization_types=[self.org_type],
        )

        unregistered_orgs = list(original_email.unregistered_organizations)
        self.assertIn(org, unregistered_orgs)

        # Test reminder creation
        reminder_email = InvitationEmailFactory(
            events=[],
            event_group=event_group,
            organization_types=[self.org_type],
            is_reminder=True,
            original_email=original_email,
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {"reminder_original_email_id": str(original_email.id)}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, reminder_email)

        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks.first().organization, org)

    def test_reminder_mixed_registration_scenarios(self):
        """Test scenarios with multiple registered & unregistered orgs."""
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")

        test_event = EventFactory(title="That one blender-mixed registration event")

        gov_org_registered = OrganizationFactory(
            organization_type=gov_type,
            government=government,
            include_in_invitation=True,
        )
        gov_org_unregistered = OrganizationFactory(
            organization_type=gov_type,
            government=government,
            include_in_invitation=True,
        )
        non_gov_registered = OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
        )
        non_gov_unregistered = OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
        )
        non_gov_null_govennment_unregistered = OrganizationFactory(
            organization_type=self.org_type,
            government=None,
            include_in_invitation=True,
        )

        # Add contacts
        gov_contact_reg = ContactFactory(organization=gov_org_registered)
        non_gov_contact_reg = ContactFactory(organization=non_gov_registered)
        ContactFactory(organization=gov_org_unregistered)
        ContactFactory(organization=non_gov_unregistered)
        ContactFactory(organization=non_gov_null_govennment_unregistered)

        # Register only 2 orgs
        RegistrationFactory(event=test_event, contact=gov_contact_reg)
        RegistrationFactory(event=test_event, contact=non_gov_contact_reg)

        # Create original email targeting all types
        original_email = InvitationEmailFactory(
            events=[test_event],
            organization_types=[gov_type, self.org_type],
        )
        # Create country invitation
        EventInvitationFactory(
            event=test_event, country=government, event_group=None, organization=None
        )
        # And create non-country invitation to reflect email
        EventInvitationFactory(
            event=test_event,
            country=None,
            event_group=None,
            organization=non_gov_null_govennment_unregistered,
        )

        unregistered_orgs = set(original_email.unregistered_organizations)

        # Check noly null-government unregistered orgs are included
        self.assertNotIn(gov_org_unregistered, unregistered_orgs)
        self.assertNotIn(non_gov_unregistered, unregistered_orgs)
        self.assertIn(non_gov_null_govennment_unregistered, unregistered_orgs)

        # Checking registered orgs, regardless of type, *are not* inclued
        self.assertNotIn(gov_org_registered, unregistered_orgs)
        self.assertNotIn(non_gov_registered, unregistered_orgs)

        # Test reminder is only sent out to unregistered orgs
        reminder_email = InvitationEmailFactory(
            events=[test_event],
            organization_types=[gov_type, self.org_type],
            is_reminder=True,
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {"reminder_original_email_id": str(original_email.id)}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, reminder_email)

        tasks = SendEmailTask.objects.all()
        unregistered_task_orgs = {task.organization for task in tasks}
        self.assertEqual(unregistered_task_orgs, {non_gov_null_govennment_unregistered})

    def test_reminder_event_group_partial_registration(self):
        """
        Test scenario with orgs registered for only one event in group;
        these orgs should not get reminder.
        """
        event_group = EventGroupFactory(name="Multi-Day Conference")
        event1 = EventFactory(title="Day 1")
        event2 = EventFactory(title="Day 2")
        event_group.events.add(event1, event2)

        government = Country.objects.first()
        org = OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
        )
        contact = ContactFactory(organization=org)
        # Register org's contact only for event1
        RegistrationFactory(event=event1, contact=contact)

        EventInvitationFactory(
            event=None, event_group=event_group, country=government, organization=None
        )

        original_email = InvitationEmailFactory(
            events=[],
            event_group=event_group,
            organization_types=[self.org_type],
        )

        # Org hould *not* be in unregistered
        self.assertNotIn(org, list(original_email.unregistered_organizations))

    def test_reminder_multiple_invitations_same_org(self):
        """Test that org invited both directly and via GOV will only get one reminder."""
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")
        org = OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
        )
        # Invite both directly and via GOV; do not register yet
        EventInvitationFactory(event=self.event, organization=org)
        EventInvitationFactory(event=self.event, country=government, organization=None)

        original_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[gov_type, self.org_type],
        )
        unregistered_orgs = list(original_email.unregistered_organizations)
        self.assertIn(org, unregistered_orgs)

        # Now register and check it's good
        contact = ContactFactory(organization=org)
        RegistrationFactory(event=self.event, contact=contact)
        self.assertNotIn(org, list(original_email.unregistered_organizations))

    def test_reminder_with_additional_cc_bcc(self):
        """Test that reminders correctly use extra CC/BCC contacts."""
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")
        # gov_org, but ruff don't like it
        OrganizationFactory(
            organization_type=gov_type,
            government=government,
            include_in_invitation=True,
        )
        gov_related_org = OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
        )
        invitation_only_cc_contact = ContactFactory(organization=gov_related_org)
        contact = ContactFactory(organization=gov_related_org)
        EventInvitationFactory(event=self.event, country=government, organization=None)
        original_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            cc_recipients=[invitation_only_cc_contact],
        )
        reminder_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            is_reminder=True,
            cc_recipients=[contact],
            bcc_recipients=[contact],
            original_email=original_email,
        )
        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {"reminder_original_email_id": str(original_email.id)}
        request._messages = FallbackStorage(request)
        self.admin.response_post_save_add(request, reminder_email)
        for task in SendEmailTask.objects.filter(email=reminder_email):
            self.assertIn(contact, task.cc_contacts.all())
            # Contact cannot be both in CC and BCC (as per services.py)
            self.assertNotIn(contact, task.bcc_contacts.all())
            self.assertNotIn(invitation_only_cc_contact, task.cc_contacts.all())
            self.assertNotIn(invitation_only_cc_contact, task.bcc_contacts.all())

    def test_reminder_multiple_orgs_same_contact_email(self):
        """
        Test scenario where different orgs' contacts have the same email address.
        Multiple reminder-related emails tasks should be generated for each org.
        """
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")

        org1 = OrganizationFactory(
            organization_type=gov_type,
            government=government,
            include_in_invitation=True,
            emails=["org1@example.com"],
        )
        org2 = OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
            emails=["org2@example.com"],
        )

        shared_email = "strangely-shared-email@example.com"
        contact1 = ContactFactory(
            organization=org1,
            emails=[shared_email],
        )
        contact2 = ContactFactory(
            organization=org2,
            emails=[shared_email],
        )
        org1.primary_contacts.add(contact1)
        org2.primary_contacts.add(contact2)

        # Create a gov-based invitation so both orgs are included
        EventInvitationFactory(event=self.event, country=government, organization=None)

        original_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[gov_type, self.org_type],
        )

        # Both orgs should be unregistered
        unregistered_orgs = set(original_email.unregistered_organizations)
        self.assertIn(org1, unregistered_orgs)
        self.assertIn(org2, unregistered_orgs)

        reminder_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[gov_type, self.org_type],
            is_reminder=True,
            original_email=original_email,
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {"reminder_original_email_id": str(original_email.id)}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, reminder_email)

        # There should be two tasks, one for each org
        tasks = SendEmailTask.objects.filter(email=reminder_email)
        self.assertEqual(tasks.count(), 2)
        orgs_in_tasks = {task.organization for task in tasks}
        self.assertSetEqual(orgs_in_tasks, {org1, org2})

        # Test field correctness for each task
        for task in tasks:
            self.assertIn(shared_email, task.email_to)
            self.assertIn(task.organization.emails[0], task.email_to)
            self.assertNotIn(shared_email, task.email_cc)
            self.assertNotIn(shared_email, task.email_bcc)

    def test_reminder_org_with_no_contacts(self):
        """Test that reminders are still created for orgs with no contacts."""
        government = Country.objects.first()
        # Creating an org but adding no contacts to it.
        org = OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
            emails=[],
        )

        EventInvitationFactory(event=self.event, country=government, organization=None)
        original_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
        )
        reminder_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            is_reminder=True,
            original_email=original_email,
        )
        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {"reminder_original_email_id": str(original_email.id)}
        request._messages = FallbackStorage(request)
        self.admin.response_post_save_add(request, reminder_email)

        # Task should not be created for the contactless :) org
        task = SendEmailTask.objects.filter(organization=org).first()
        self.assertIsNone(task)
        messages_list = list(get_messages(request))
        self.assertIn("reminder emails scheduled", str(messages_list[0]))

    def test_reminder_excludes_orgs_with_include_in_invitation_false(self):
        """
        Test that orgs with include_in_invitation=False are not included in reminders.
        This should happen regardless of the flag setting time.
        """
        government = Country.objects.first()
        org = OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            include_in_invitation=False,
        )
        EventInvitationFactory(event=self.event, country=government, organization=None)
        original_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
        )
        self.assertNotIn(org, list(original_email.unregistered_organizations))
        reminder_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            is_reminder=True,
            original_email=original_email,
        )
        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {"reminder_original_email_id": str(original_email.id)}
        request._messages = FallbackStorage(request)
        self.admin.response_post_save_add(request, reminder_email)

        # No task should be created for uninvitable org
        task = SendEmailTask.objects.filter(organization=org).first()
        self.assertIsNone(task)

    def test_reminder_org_with_only_cc_bcc_contacts(self):
        """
        Test scenario where org only has CC/BCC contacts and no 'to' emails.
        No task should (hopefully) be created in this case.
        """
        government = Country.objects.first()
        org = OrganizationFactory(
            organization_type=self.org_type,
            government=government,
            include_in_invitation=True,
            emails=[],
            email_ccs=["cc@example.com"],
        )
        # Add a contact with only CC emails
        contact = ContactFactory(
            organization=org,
            emails=[],
            email_ccs=["contact-cc@example.com"],
        )
        org.primary_contacts.add(contact)

        EventInvitationFactory(event=self.event, country=government, organization=None)
        original_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
        )
        reminder_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[self.org_type],
            is_reminder=True,
            original_email=original_email,
        )
        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {"reminder_original_email_id": str(original_email.id)}
        request._messages = FallbackStorage(request)
        self.admin.response_post_save_add(request, reminder_email)

        # No task should be created
        task = SendEmailTask.objects.filter(organization=org).first()
        self.assertIsNone(task)
        messages_list = list(get_messages(request))
        self.assertIn("reminder emails scheduled", str(messages_list[0]))

    def test_reminders_with_countryless_gov_organization(self):
        """
        Test that reminding both "normal" and countryless GOV organizations results in
        proper handling of all related organizations.
        """
        government = Country.objects.first()
        gov_type = OrganizationType.objects.get(acronym="GOV")

        # Create a GOV organization
        gov_org = OrganizationFactory(
            name="Government Org",
            organization_type=gov_type,
            government=government,
        )

        # Create related organization in same country
        related_org1 = OrganizationFactory(
            name="Related Org 1",
            organization_type=self.org_type,
            government=government,
        )

        # Create a GOV organization with no country
        countryless_gov_org = OrganizationFactory(
            name="Countryless Government Org",
            organization_type=gov_type,
            government=None,
        )

        # Add contacts to organizations
        gov_contact = ContactFactory(
            organization=gov_org,
        )
        related_contact1 = ContactFactory(organization=related_org1)

        gov_org.primary_contacts.add(gov_contact)
        related_org1.primary_contacts.add(related_contact1)

        # Create invitation email & related invitations
        invitation_email = InvitationEmailFactory(
            events=[self.event],
            organization_types=[gov_type],
        )
        EventInvitationFactory(event=self.event, country=government, organization=None)
        # This one is for the government-less GOV org
        EventInvitationFactory(
            event=self.event, country=None, organization=countryless_gov_org
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, invitation_email)

        # Get created tasks
        tasks = SendEmailTask.objects.all()

        # Should create 2 reminder tasks - one for countryless GOV, other for all others
        self.assertEqual(tasks.count(), 2)

        # Check country-linked invitation
        task = tasks.filter(invitation__country__isnull=False).first()
        self.assertIsNotNone(task)
        self.assertEqual(task.organization, gov_org)
        self.assertEqual(task.invitation.country, government)
        self.assertIsNone(task.invitation.organization)

        # Check organization-linked invitation
        task = tasks.filter(invitation__country__isnull=True).first()
        self.assertIsNotNone(task)
        self.assertIsNotNone(task.invitation.organization)
        self.assertEqual(task.organization, countryless_gov_org)
        self.assertIsNone(task.invitation.country)

    def test_reminders_organizations_list(self):
        """Test that reminders work with specific organizations list."""
        org1 = OrganizationFactory(
            organization_type=self.org_type, emails=["org1@example.com"]
        )
        org2 = OrganizationFactory(
            organization_type=self.org_type, emails=["org2@example.com"]
        )

        contact1 = ContactFactory(organization=org1, emails=["contact1@example.com"])
        ContactFactory(organization=org2, emails=["contact2@example.com"])

        # Register only org1
        RegistrationFactory(event=self.event, contact=contact1)

        # Create invitations
        EventInvitationFactory(event=self.event, organization=org1)
        EventInvitationFactory(event=self.event, organization=org2)

        original_email = InvitationEmailFactory(
            events=[self.event],
            organizations=[org1, org2],
            organization_types=[],
        )

        # Only org2 should be unregistered
        unregistered_orgs = list(original_email.unregistered_organizations)
        self.assertIn(org2, unregistered_orgs)
        self.assertNotIn(org1, unregistered_orgs)

        # Create reminder
        reminder_email = InvitationEmailFactory(
            events=[self.event],
            organizations=[org1, org2],
            organization_types=[],
            is_reminder=True,
            original_email=original_email,
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {"reminder_original_email_id": str(original_email.id)}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, reminder_email)

        # There should only be a task for org2 (the unregistered one)
        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 1)
        self.assertEqual(tasks.first().organization, org2)

    def test_reminder_organizations_list_include_flag(self):
        """
        Test include_in_invitation is not taken into account for reminders with specific
        organizations list.
        """
        org1 = OrganizationFactory(
            organization_type=self.org_type,
            emails=["org1@example.com"],
            include_in_invitation=True,
        )
        org2 = OrganizationFactory(
            organization_type=self.org_type,
            emails=["org2@example.com"],
            include_in_invitation=False,
        )

        ContactFactory(organization=org1, emails=["contact1@example.com"])
        ContactFactory(organization=org2, emails=["contact2@example.com"])

        # Create invitations
        EventInvitationFactory(event=self.event, organization=org1)
        EventInvitationFactory(event=self.event, organization=org2)
        original_email = InvitationEmailFactory(
            events=[self.event],
            organizations=[org1, org2],
            organization_types=[],
        )

        # Both organizations should be unregistered
        unregistered_orgs = set(original_email.unregistered_organizations)
        self.assertSetEqual({org1, org2}, unregistered_orgs)

        # Create reminder
        reminder_email = InvitationEmailFactory(
            events=[self.event],
            organizations=[org1, org2],
            organization_types=[],
            is_reminder=True,
            original_email=original_email,
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {"reminder_original_email_id": str(original_email.id)}
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, reminder_email)

        # There should be tasks for both orgs, regardless of include flag
        tasks = SendEmailTask.objects.all()
        self.assertEqual(tasks.count(), 2)
        self.assertSetEqual(
            {t.organization for t in tasks},
            {org1, org2},
        )


class TestInvitationEmailAdminAutocompleteEvents(TestCase):
    """Test autocomplete querysets for events and event groups."""

    fixtures = ["initial/country"]

    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_superuser(
            email="eventful-admin@example.com", password="eventful-password"
        )

        self.site = AdminSite()
        self.admin = InvitationEmailAdmin(InvitationEmail, self.site)

        now = timezone.now()
        self.today_end_datetime = now.replace(hour=23, minute=59, second=59)
        self.yesterday = now - timedelta(days=1)
        self.tomorrow = now + timedelta(days=1)
        self.next_week = now + timedelta(days=7)
        self.last_week = now - timedelta(days=7)

    def test_events_field_queryset(self):
        """Test that the events field only shows future events in autocomplete."""

        past_event = EventFactory(
            code="PAST_TEST_EVENT",
            title="Nostalgia Event",
            start_date=self.yesterday - timedelta(days=5),
            end_date=self.yesterday,
        )

        ending_today = EventFactory(
            code="TODAY_TEST_EVENT",
            title="Carpe Diem - ending today",
            start_date=self.yesterday,
            end_date=self.today_end_datetime,
        )

        future_event = EventFactory(
            code="FUTURE_TEST_EVENT",
            title="Futuristic Event",
            start_date=self.tomorrow,
            end_date=self.next_week,
        )

        event_admin = EventAdmin(Event, self.site)

        # Inject needed params in the search request (invitation email as referrer)
        request = self.factory.get("/admin/events/event/autocomplete/")
        request.user = self.user
        request.META["HTTP_REFERER"] = "/admin/emails/invitationemail/add/"

        # Unfortunately I found no good way of testing the returned results via backend
        all_events = Event.objects.filter(code__contains="TEST_EVENT")
        filtered_queryset, _ = event_admin.get_search_results(
            request, all_events, "TEST_EVENT"
        )
        event_codes = set(filtered_queryset.values_list("code", flat=True))

        self.assertNotIn(past_event.code, event_codes)
        self.assertIn(ending_today.code, event_codes)
        self.assertIn(future_event.code, event_codes)
