from datetime import UTC, datetime

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
        request.session = "session"
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


class TestInvitationEmailAdminGovBehaviour(TestCase):
    """Test class for GOV-related behaviour in InvitationEmails."""

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
        request.session = "session"
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
        request.session = "session"
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
        request.session = "session"
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
        request.session = "session"
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
        request.session = "session"
        request._messages = FallbackStorage(request)

        self.admin.response_post_save_add(request, invitation_email)

        tasks = SendEmailTask.objects.all()

        # Should create 2 tasks for each organization
        self.assertEqual(tasks.count(), 2)

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
        request.session = "session"
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
