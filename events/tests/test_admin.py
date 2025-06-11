from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.urls import reverse

from api.tests.factories import (
    ContactFactory,
    EventFactory,
    EventGroupFactory,
    EventInvitationFactory,
    OrganizationFactory,
    RegistrationFactory,
)
from core.models import Country, OrganizationType
from emails.models import SendEmailTask
from emails.tests.factories import InvitationEmailFactory
from events.admin import EventInvitationAdmin, FutureEventFilter, HasUnregisteredFilter
from events.models import EventInvitation


class TestEventInvitationAdmin(TestCase):
    fixtures = [
        "initial/country",
        "initial/organizationtype",
        "initial/registrationstatus",
        "initial/registrationrole",
    ]

    def setUp(self):
        self.site = AdminSite()
        self.admin = EventInvitationAdmin(EventInvitation, self.site)
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="password"
        )

        self.future_date = datetime(2026, 1, 1, tzinfo=UTC)
        self.past_date = datetime(2024, 1, 1, tzinfo=UTC)

        self.gov_type = OrganizationType.objects.get(acronym="GOV")
        self.org_type = OrganizationType.objects.exclude(acronym="GOV").first()
        self.country = Country.objects.first()
        self.event = EventFactory(
            title="Test Event",
            start_date=self.future_date,
            end_date=self.future_date + timedelta(days=3),
            venue_country=self.country,
        )
        self.event_group = EventGroupFactory(name="Test Group")
        self.event_group.events.add(self.event)

        self.organization = OrganizationFactory(
            name="Test Org",
            organization_type=self.org_type,
            emails=["org@example.com"],
            government=None,
        )
        self.gov_org = OrganizationFactory(
            name="Gov Org",
            organization_type=self.gov_type,
            emails=["gov@example.com"],
            government=self.country,
        )

        self.contact = ContactFactory(
            organization=self.organization,
            emails=["contact@example.com"],
        )
        self.gov_contact = ContactFactory(
            organization=self.gov_org,
            emails=["gov-contact@example.com"],
        )

        self.invitation = EventInvitationFactory(
            event=self.event,
            event_group=None,
            organization=self.organization,
            country=None,
        )
        self.gov_invitation = EventInvitationFactory(
            event=self.event,
            event_group=None,
            organization=None,
            country=self.country,
        )

        self.email = InvitationEmailFactory(
            subject="Test Email",
            content="Test content",
        )

    def test_unregistered_organizations_display(self):
        """Test the unregistered_organizations_display method."""
        # Test using invitation that has no registrations (non-GOV org)
        html = self.admin.unregistered_organizations_display(self.invitation)
        self.assertIn(self.organization.name, html)
        self.assertIn(
            reverse("admin:core_organization_change", args=[self.organization.id]), html
        )
        self.assertIn("Send Reminder Email to All", html)

        # Add registration to make org "invited"; test that display changes
        RegistrationFactory(
            contact=self.contact,
            event=self.event,
        )
        html = self.admin.unregistered_organizations_display(self.invitation)
        self.assertIn("All organizations have registered", html)
        self.assertNotIn("Send Reminder Email to All", html)

        # Now test GOV invitation with no registrations
        html = self.admin.unregistered_organizations_display(self.gov_invitation)
        self.assertIn(self.gov_org.name, html)
        self.assertIn("Send Reminder Email to All", html)

        # Add registration for GOV org & re-test
        RegistrationFactory(
            contact=self.gov_contact,
            event=self.event,
        )
        html = self.admin.unregistered_organizations_display(self.gov_invitation)
        self.assertIn("All organizations have registered", html)

    def test_send_reminder_emails_single_invitation(self):
        """Test the send_reminder_emails action with a single invitation."""
        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        messages = FallbackStorage(request)
        request._messages = messages

        # Call the action with a queryset containing one invitation
        queryset = EventInvitation.objects.filter(id=self.invitation.id)
        response = self.admin.send_reminder_emails(request, queryset)

        # Check for the success message being present in the request
        messages_list = list(get_messages(request))
        self.assertEqual(len(messages_list), 1)
        self.assertIn("Preparing to send reminders", str(messages_list[0]))
        self.assertIn("1 unregistered", str(messages_list[0]))

        # Check redirect to invitation email with proper parameters
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/emails/invitationemail/add/", response.url)
        self.assertIn("is_reminder=1", response.url)
        self.assertIn(f"invitation_id={self.invitation.id}", response.url)

    def test_send_reminder_emails_multiple_invitations(self):
        """Test the send_reminder_emails action rejects multiple invitations."""
        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        messages = FallbackStorage(request)
        request._messages = messages

        queryset = EventInvitation.objects.all()
        self.assertGreater(queryset.count(), 1)

        response = self.admin.send_reminder_emails(request, queryset)

        # Check for warning message
        messages_list = list(get_messages(request))
        self.assertEqual(len(messages_list), 1)
        self.assertIn("Please select only one invitation", str(messages_list[0]))

        # Check that no redirect happened
        self.assertIsNone(response)

        # Check that no session data was set
        self.assertNotIn("reminder_invitation_id", request.session)

    def test_send_reminder_emails_no_unregistered(self):
        """Test the action when all organizations have registered."""
        RegistrationFactory(
            contact=self.contact,
            event=self.event,
        )
        RegistrationFactory(
            contact=self.gov_contact,
            event=self.event,
        )

        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        messages = FallbackStorage(request)
        request._messages = messages

        # Call the action with a queryset containing one invitation
        queryset = EventInvitation.objects.filter(id=self.invitation.id)
        response = self.admin.send_reminder_emails(request, queryset)

        # Check for info message
        messages_list = list(get_messages(request))
        self.assertEqual(len(messages_list), 1)
        self.assertIn("No unregistered organizations found", str(messages_list[0]))

        # Check that no redirect happened
        self.assertIsNone(response)

        # Check that no session data was set
        self.assertNotIn("reminder_invitation_id", request.session)

    @patch("events.admin.redirect")
    def test_reminder_url_formation(self, mock_redirect):
        """Test that the reminder URL is formed correctly."""
        request = self.factory.post("/fake-url/")
        request.user = self.user
        request.session = {}
        request._messages = FallbackStorage(request)

        # Call the admin action
        queryset = EventInvitation.objects.filter(id=self.invitation.id)
        self.admin.send_reminder_emails(request, queryset)

        # Check that redirect was called with correct URL
        mock_redirect.assert_called_once()
        args = mock_redirect.call_args[0][0]
        self.assertIn("/admin/emails/invitationemail/add/", args)
        self.assertIn("is_reminder=1", args)
        self.assertIn(f"invitation_id={self.invitation.id}", args)

    def test_event_or_group_display(self):
        """Test the event_or_group display method."""
        self.assertEqual(self.admin.event_or_group(self.invitation), self.event)

        # Test using event group
        group_invitation = EventInvitationFactory(
            event=None,
            event_group=self.event_group,
            organization=self.organization,
        )
        self.assertEqual(self.admin.event_or_group(group_invitation), self.event_group)

    def test_invitation_link_display(self):
        """Test the invitation_link display method."""
        html = self.admin.invitation_link(self.invitation)
        self.assertIn(str(self.invitation.token), html)
        self.assertIn("View Invitation Link", html)

    def test_is_for_future_event_display(self):
        """Test the is_for_future_event_display method."""
        # Future event should return True
        self.assertTrue(self.admin.is_for_future_event_display(self.invitation))

        # Past event should return False
        past_event = EventFactory(
            title="Past Event",
            start_date=datetime(2020, 1, 1, tzinfo=UTC),
            end_date=datetime(2020, 1, 2, tzinfo=UTC),
        )
        past_invitation = EventInvitationFactory(
            event=past_event,
            organization=self.organization,
        )
        self.assertFalse(self.admin.is_for_future_event_display(past_invitation))

    def test_email_tasks_display(self):
        """Test the email_tasks_display method."""
        # Without any tasks
        self.assertEqual(self.admin.email_tasks_display(self.invitation), "-")

        # With tasks
        SendEmailTask.objects.create(
            invitation=self.invitation,
            organization=self.organization,
            email=self.email,
        )
        html = self.admin.email_tasks_display(self.invitation)
        self.assertIn("1 tasks", html)
        self.assertIn(f"invitation__id__exact={self.invitation.id}", html)

    def test_has_unregistered_filter(self):
        """Testing HasUnregisteredFilter."""
        request = self.factory.get("/fake-url/")
        list_filter = HasUnregisteredFilter(
            request, params={}, model=EventInvitation, model_admin=self.admin
        )
        list_filter.used_parameters = {list_filter.parameter_name: "yes"}

        # Test with "yes" value (has unregistered)
        queryset = EventInvitation.objects.all()
        filtered = list_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 2)

        # Add registration for one invitation
        RegistrationFactory(
            contact=self.contact,
            event=self.event,
        )

        # Test that filter now excludes the invitation with registration
        filtered = list_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.gov_invitation)

        # Test with "no" value (all registered)
        no_filter = HasUnregisteredFilter(
            request, params={}, model=EventInvitation, model_admin=self.admin
        )
        no_filter.used_parameters = {no_filter.parameter_name: "no"}
        filtered = no_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), self.invitation)

        # Add registration for the other invitation
        RegistrationFactory(
            contact=self.gov_contact,
            event=self.event,
        )

        # Filter for "yes" should now return empty
        filtered = list_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 0)

        # Filter for "no" should return both
        filtered = no_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 2)

    def test_future_event_filter(self):
        """Test the FutureEventFilter."""
        # Create filter instance for future events
        request = self.factory.get("/fake-url/")
        future_params = {FutureEventFilter.parameter_name: "future"}

        for invitation in [self.invitation, self.gov_invitation]:
            self.assertTrue(invitation.is_for_future_event)

        future_filter = FutureEventFilter(
            request, future_params, model=EventInvitation, model_admin=self.admin
        )

        # Test with "future" value
        queryset = EventInvitation.objects.all()
        filtered = future_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 2)

        # Add a past event and invitation
        past_event = EventFactory(
            title="Past Event",
            start_date=self.past_date,
            end_date=self.past_date + timedelta(days=3),
        )
        past_invitation = EventInvitationFactory(
            event=past_event,
            organization=self.organization,
            country=None,
        )
        self.assertFalse(past_invitation.is_for_future_event)

        queryset = EventInvitation.objects.all()
        self.assertEqual(queryset.count(), 3)

        # Past invitation should be excluded from "future" query
        future_filter = FutureEventFilter(
            request, params={}, model=EventInvitation, model_admin=self.admin
        )
        future_filter.used_parameters = {future_filter.parameter_name: "future"}
        filtered = future_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 2)
        self.assertNotIn(past_invitation, filtered)

        # Filter should only include past invitation for "past" query
        past_filter = FutureEventFilter(
            request, params={}, model=EventInvitation, model_admin=self.admin
        )
        past_filter.used_parameters = {past_filter.parameter_name: "past"}
        filtered = past_filter.queryset(request, queryset)
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), past_invitation)
