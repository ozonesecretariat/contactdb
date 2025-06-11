import json

from django.utils import timezone
from rest_framework.reverse import reverse as api_reverse

from api.tests.base import BaseAPITestCase
from api.tests.factories import (
    ContactFactory,
    EventFactory,
    EventGroupFactory,
    EventInvitationFactory,
    OrganizationFactory,
    RegistrationFactory,
    RegistrationRoleFactory,
    RegistrationStatusFactory,
)
from api.views.event import get_nomination_status_id
from core.models import Organization
from events.models import Registration


class TestEventsAPI(BaseAPITestCase):
    url = "/api/events/"
    fixtures = [
        *BaseAPITestCase.fixtures,
        "initial/region",
        "initial/subregion",
        "initial/country",
        "test/event",
    ]

    def test_get_events_admin(self):
        self.login_admin()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 20)

    def test_get_events_email_user(self):
        self.login_emails_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 20)

    def test_get_events_no_access(self):
        self.login_no_access_user()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


class TestEventNominationsAPI(BaseAPITestCase):
    fixtures = [
        *BaseAPITestCase.fixtures,
        "initial/region",
        "initial/subregion",
        "initial/country",
        "initial/organizationtype",
        "test/event",
        "test/organization",
    ]

    @classmethod
    def setUpTestData(cls):
        """Sets up common data for all tests in this class."""
        super().setUpTestData()
        # Status needs to be created as it's referenced by all registrations
        cls.nomination_status = RegistrationStatusFactory(name="Nominated")
        cls.role = RegistrationRoleFactory(name="Participant")

    def setUp(self):
        super().setUp()

        self.organization = OrganizationFactory()

        self.contact1 = ContactFactory(
            organization=self.organization,
            first_name="Test",
            last_name="Contact1",
            emails=["test1@example.com"],
        )
        self.contact2 = ContactFactory(
            organization=self.organization,
            first_name="Test",
            last_name="Contact2",
            emails=["test2@example.com"],
        )

        self.event = EventFactory()
        self.invitation = EventInvitationFactory(
            event=self.event, organization=self.organization
        )
        self.url = api_reverse(
            "events-nominations-detail",
            kwargs={"token": self.invitation.token},
        )

    def test_get_nominations_list(self):
        """Test retrieving nominations list."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    def test_get_available_contacts(self):
        """Test retrieving available contacts for nomination."""
        response = self.client.get(f"{self.url}available-contacts/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["emails"], ["test1@example.com"])

    def test_nominate_contacts(self):
        """Test nominating contacts."""
        data = {
            "events": [self.event.code],
            "nominations": [
                {
                    "contact": self.contact1.id,
                    "is_funded": True,
                    "role": self.role.id,
                    "priority_pass_code": "ABC123",
                },
                {"contact": self.contact2.id, "is_funded": False, "role": self.role.id},
            ],
        }
        response = self.client.post(
            f"{self.url}nominate-contacts/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Verify registrations were created
        registrations = Registration.objects.all()
        self.assertEqual(registrations.count(), 2)
        self.assertEqual(registrations.filter(contact=self.contact1).exists(), True)

    def test_nominate_invalid_contact(self):
        """Test nominating a contact from another organization."""
        other_org = Organization.objects.create(name="Other Org")
        other_contact = ContactFactory(
            organization=other_org,
            first_name="Other",
            last_name="Contact",
            emails=["other@example.com"],
        )

        data = {
            "events": [self.event.code],
            "nominations": [
                {
                    "contact": other_contact.id,
                    "is_funded": True,
                    "role": self.role.id,
                    "priority_pass_code": "ABC123",
                }
            ],
        }
        response = self.client.post(
            f"{self.url}nominate-contacts/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Registration.objects.count(), 0)

    def test_invalid_token(self):
        """Test accessing nominations with invalid UUID token."""
        invalid_url = api_reverse(
            "events-nominations-detail",
            # Not a valid token, but has UUID format
            kwargs={"token": "12345678-1234-5678-1234-567812345678"},
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_non_uuid_token(self):
        """
        Test accessing nominations with invalid non-UUID token.

        This should still yield a "not found" error to not give away too much.
        """
        invalid_url = api_reverse(
            "events-nominations-detail", kwargs={"token": "invalid_token"}
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_nomination_with_event_group(self):
        """Test nominations with event group instead of single event."""
        event_group = EventGroupFactory(name="Test Group", events=[self.event])
        new_invitation = EventInvitationFactory(
            event=None, event_group=event_group, organization=self.organization
        )

        # Create a registration for one of the events in the group
        RegistrationFactory(
            event=self.event,
            contact=self.contact1,
            status=self.nomination_status,
            role=self.role,
        )

        url = api_reverse(
            "events-nominations-detail",
            kwargs={"token": new_invitation.token},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_get_registrations(self):
        """Test retrieving *existing* registrations for an invitation."""
        RegistrationFactory(
            event=self.event,
            contact=self.contact1,
            status_id=get_nomination_status_id(),
            date=timezone.now(),
        )
        RegistrationFactory(
            event=self.event,
            contact=self.contact2,
            status_id=get_nomination_status_id(),
            date=timezone.now(),
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["contact"]["id"], self.contact1.id)
        self.assertEqual(data[1]["contact"]["id"], self.contact2.id)
