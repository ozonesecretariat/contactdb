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
from core.models import Country, Organization, OrganizationType
from events.models import Registration


class TestEventsAPI(BaseAPITestCase):
    url = "/api/events/"
    fixtures = [
        *BaseAPITestCase.fixtures,
        "initial/region",
        "initial/subregion",
        "initial/country",
        "test/eventgroup",
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
        "test/eventgroup",
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
        cls.role_delegate = RegistrationRoleFactory(name="Delegate")

    def setUp(self):
        super().setUp()

        self.organization = OrganizationFactory()
        self.organization2 = OrganizationFactory()

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

    def test_get_available_contacts_country_invitation(self):
        """
        Test that all org contacts in the country are available
        for country-level invitations.
        """
        ro = Country.objects.get(code="RO")
        gov = OrganizationType.objects.get(acronym="GOV")
        ass = OrganizationType.objects.get(acronym="ASS-PANEL")

        org1 = OrganizationFactory(government=ro, organization_type=gov)
        org2 = OrganizationFactory(government=ro, organization_type=ass)
        org3 = OrganizationFactory()

        contact1 = ContactFactory(organization=org1)
        contact2 = ContactFactory(organization=org2)
        contact3 = ContactFactory(organization=org3)

        invitation = EventInvitationFactory(
            event=self.event, country=ro, organization=None
        )
        url = api_reverse(
            "events-nominations-available-contacts",
            kwargs={"token": invitation.token},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        ids = {c["id"] for c in response.json()}
        self.assertIn(contact1.id, ids)
        self.assertIn(contact2.id, ids)
        self.assertNotIn(contact3.id, ids)

    def test_nominate_contact(self):
        """Test nominating contact."""
        data = [
            {
                "event": self.event.code,
                "contact": self.contact1.id,
                "role": self.role.name,
            },
        ]
        response = self.client.post(
            f"{self.url}nominate-contact/{self.contact1.id}/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Verify registrations were created
        registrations = Registration.objects.all()
        self.assertEqual(registrations.count(), 1)
        self.assertEqual(registrations.filter(contact=self.contact1).exists(), True)

        # Check returned data
        response_data = response.json()
        self.assertEqual(len(response_data), 1)

    def test_nominate_contact_event_group(self):
        """Test nominating contact."""
        ev1 = EventFactory()
        ev2 = EventFactory()

        event_group = EventGroupFactory(name="Test Group", events=[ev1, ev2])
        new_invitation = EventInvitationFactory(
            event=None, event_group=event_group, organization=self.organization
        )

        data = [
            {
                "event": ev2.code,
                "contact": self.contact1.id,
                "role": self.role.name,
            },
            {
                "event": ev1.code,
                "contact": self.contact1.id,
                "role": self.role.name,
            },
        ]
        url = api_reverse(
            "events-nominations-nominate-contact",
            kwargs={"token": new_invitation.token, "contact_id": self.contact1.id},
        )
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Verify registrations were created
        registrations = Registration.objects.all()
        self.assertEqual(registrations.count(), 2)
        self.assertEqual(
            registrations.filter(contact=self.contact1, event=ev1).exists(), True
        )
        self.assertEqual(
            registrations.filter(contact=self.contact1, event=ev2).exists(), True
        )

        # Check returned data
        response_data = response.json()
        self.assertEqual(len(response_data), 2)

    def test_update_nominations_event_group(self):
        ev1 = EventFactory()
        ev2 = EventFactory()
        ev3 = EventFactory()

        event_group = EventGroupFactory(name="Test Group", events=[ev1, ev2, ev3])
        new_invitation = EventInvitationFactory(
            event=None, event_group=event_group, organization=self.organization
        )
        RegistrationFactory(contact=self.contact1, event=ev2, role=self.role)
        RegistrationFactory(contact=self.contact1, event=ev3, role=self.role)

        data = [
            {
                "event": ev2.code,
                "contact": self.contact1.id,
                "role": self.role.name,
            },
            {
                "event": ev1.code,
                "contact": self.contact1.id,
                "role": self.role_delegate.name,
            },
        ]
        url = api_reverse(
            "events-nominations-nominate-contact",
            kwargs={"token": new_invitation.token, "contact_id": self.contact1.id},
        )
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Verify registrations were created
        registrations = Registration.objects.all()
        self.assertEqual(registrations.count(), 2)
        self.assertEqual(
            registrations.filter(
                contact=self.contact1, event=ev1, role=self.role_delegate
            ).exists(),
            True,
        )
        self.assertEqual(
            registrations.filter(
                contact=self.contact1, event=ev2, role=self.role
            ).exists(),
            True,
        )
        self.assertEqual(
            registrations.filter(contact=self.contact1, event=ev3).exists(), False
        )

        # Check returned data
        response_data = response.json()
        self.assertEqual(len(response_data), 2)

    def test_nominate_contacts_country_invitation(self):
        """Test that nomination works for any org contact with government == country."""
        ro = Country.objects.get(code="RO")
        gov = OrganizationType.objects.get(acronym="GOV")
        ass = OrganizationType.objects.get(acronym="ASS-PANEL")

        org1 = OrganizationFactory(government=ro, organization_type=gov)
        org2 = OrganizationFactory(government=ro, organization_type=ass)
        contact1 = ContactFactory(organization=org1)
        contact2 = ContactFactory(organization=org2)

        invitation = EventInvitationFactory(
            event=self.event, country=ro, organization=None
        )
        nomination_data_1 = [
            {
                "event": self.event.code,
                "contact": contact1.id,
                "is_funded": True,
                "role": self.role.name,
                "priority_pass_code": "ABC123",
            }
        ]
        nomination_data_2 = [
            {
                "event": self.event.code,
                "contact": contact2.id,
                "is_funded": False,
                "role": self.role.name,
            },
        ]
        url = api_reverse(
            "events-nominations-nominate-contact",
            kwargs={"token": invitation.token, "contact_id": contact1.id},
        )
        response = self.client.post(
            url, data=json.dumps(nomination_data_1), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        url = api_reverse(
            "events-nominations-nominate-contact",
            kwargs={"token": invitation.token, "contact_id": contact2.id},
        )
        response = self.client.post(
            url, data=json.dumps(nomination_data_2), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Registration.objects.filter(contact=contact1, event=self.event).exists()
        )
        self.assertTrue(
            Registration.objects.filter(contact=contact2, event=self.event).exists()
        )

    def test_nominate_invalid_contact(self):
        """Test nominating a contact from another organization."""
        other_org = Organization.objects.create(name="Other Org")
        other_contact = ContactFactory(
            organization=other_org,
            first_name="Other",
            last_name="Contact",
            emails=["other@example.com"],
        )

        data = [
            {
                "contact": other_contact.id,
                "event": self.event.code,
                "role": self.role.name,
            }
        ]
        response = self.client.post(
            f"{self.url}nominate-contact/{other_contact.id}/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Registration.objects.count(), 0)

    def test_nominate_invalid_contact_data(self):
        """Test nominating a contact from another organization."""
        other_org = Organization.objects.create(name="Other Org")
        other_contact = ContactFactory(
            organization=other_org,
            first_name="Other",
            last_name="Contact",
            emails=["other@example.com"],
        )

        data = [
            {
                "contact": other_contact.id,
                "event": self.event.code,
                "role": self.role.name,
            }
        ]
        response = self.client.post(
            f"{self.url}nominate-contact/{self.contact1.id}/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Registration.objects.count(), 0)

    def test_nominate_invalid_event(self):
        """Test nominating a contact from another organization."""
        other_event = EventFactory()
        data = [
            {
                "contact": self.contact1.id,
                "event": other_event.code,
                "role": self.role.name,
            }
        ]
        response = self.client.post(
            f"{self.url}nominate-contact/{self.contact1.id}/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
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
            date=timezone.now(),
        )
        RegistrationFactory(
            event=self.event,
            contact=self.contact2,
            date=timezone.now(),
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["contact"]["id"], self.contact1.id)
        self.assertEqual(data[1]["contact"]["id"], self.contact2.id)

    def test_list_organizations(self):
        url = api_reverse(
            "events-nominations-organizations",
            kwargs={"token": self.invitation.token},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_list_organization_gov(self):
        ro = Country.objects.get(code="RO")
        fr = Country.objects.get(code="FR")
        gov = OrganizationType.objects.get(acronym="GOV")
        ass = OrganizationType.objects.get(acronym="ASS-PANEL")

        org1 = OrganizationFactory(government=ro, organization_type=gov)
        org2 = OrganizationFactory(government=ro, organization_type=ass)
        OrganizationFactory(government=fr, organization_type=gov)

        new_invitation = EventInvitationFactory(
            event=self.event,
            country=ro,
            organization=None,
            event_group=None,
        )
        url = api_reverse(
            "events-nominations-organizations",
            kwargs={"token": new_invitation.token},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        result = response.json()

        self.assertEqual(len(result), 2)
        org_ids = {org1.id, org2.id}
        self.assertTrue(all(org["id"] in org_ids for org in result))

    def test_create_contact(self):
        url = api_reverse(
            "events-nominations-create-contact",
            kwargs={"token": self.invitation.token},
        )
        response = self.client.post(
            url,
            {
                "firstName": "John",
                "lastName": "Doe",
                "emails": ["test-create@example.com"],
                "organization": self.organization.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        self.assertTrue(
            self.organization.contacts.filter(
                emails=["test-create@example.com"]
            ).exists()
        )

    def test_create_contact_government_related_orgs(self):
        ro = Country.objects.get(code="RO")
        fr = Country.objects.get(code="FR")
        gov = OrganizationType.objects.get(acronym="GOV")
        ass = OrganizationType.objects.get(acronym="ASS-PANEL")

        OrganizationFactory(government=ro, organization_type=gov)
        org2 = OrganizationFactory(government=ro, organization_type=ass)
        org3 = OrganizationFactory(government=fr, organization_type=gov)

        new_invitation = EventInvitationFactory(
            event=self.event,
            country=ro,
            organization=None,
            event_group=None,
        )

        # RO government-related org, should work
        url = api_reverse(
            "events-nominations-create-contact",
            kwargs={"token": new_invitation.token},
        )
        response = self.client.post(
            url,
            {
                "emails": ["test-create@example.com"],
                "organization": org2.id,
                "firstName": "John",
                "lastName": "Doe",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        # FR government-related org, should not work
        response = self.client.post(
            url,
            {
                "emails": ["test-create@example.com"],
                "organization": org3.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
