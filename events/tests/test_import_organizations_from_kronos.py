from copy import deepcopy
from unittest.mock import patch

from django.test import TestCase

from core.models import Contact, Organization
from events.models import LoadOrganizationsFromKronosTask


class TestImportOrganizations(TestCase):
    fixtures = [
        "initial/region",
        "initial/subregion",
        "initial/country",
        "initial/organizationtype",
    ]

    def setUp(self):
        self.fake_org = {
            "acronym": "",
            "country": "ao",
            "countryName": "Angola",
            "government": "pl",
            "governmentName": "Poland",
            "name": "The Society of Whimsical Antics and Nonsensical Endeavors",
            "organizationId": "11111111111",
            "organizationType": "GOV",
            "organizationTypeId": "594bce8cf939e087ce7d5fef",
            "memberCount": 32,
            "eventCount": 0,
            "address": "real place",
            "city": "Vienna",
            "state": "",
            "postalCode": "123456789",
            "phones": [],
            "faxes": [],
            "emails": ["zephyr.m@example.com"],
            "emailCcs": ["fly.away@zephyr.song"],
            "webs": [],
            "notes": "",
            "isCheckNotes": False,
            "isValidated": False,
            "validatedBy": "Unknown",
            "validations": [],
            "isDateOfBirthRequired": False,
            "isHidden": False,
            "createdOn": "2017-07-03T09:15:31.036Z",
            "createdBy": "",
            "updatedOn": "2025-03-07T08:38:18.875Z",
            "updatedBy": "",
        }

        self.mock_data = [self.fake_org]
        self.mock_client = patch("events.parsers.KronosClient").start()
        self.mock_client.return_value.get_all_organizations.side_effect = (
            lambda *args: deepcopy(self.mock_data)
        )

    def tearDown(self):
        patch.stopall()

    def load_organizations(self):
        LoadOrganizationsFromKronosTask.objects.create().run(is_async=False)

    def test_load_new_organization(self):
        self.load_organizations()

        self.assertEqual(Organization.objects.count(), 1)
        organization = Organization.objects.first()
        self.assertEqual(
            organization.name,
            "The Society of Whimsical Antics and Nonsensical Endeavors",
        )
        self.assertEqual(organization.country.name, "Angola")
        self.assertEqual(organization.government.name, "Poland")
        self.assertEqual(organization.address, "real place")
        self.assertEqual(organization.postal_code, "123456789")
        self.assertEqual(organization.emails, ["zephyr.m@example.com"])

        self.assertEqual(organization.primary_contacts.count(), 0)
        self.assertEqual(organization.include_in_invitation, False)

    def test_load_existing_organization(self):
        self.load_organizations()
        self.assertEqual(Organization.objects.count(), 1)
        self.load_organizations()
        self.assertEqual(Organization.objects.count(), 1)

    def test_primary_contacts_added(self):
        contact = Contact.objects.create(
            organization=None,
            first_name="Zephyr",
            last_name="Moonweaver",
            emails=["zephyr.m@example.com", "another@uninteresting.org"],
        )
        self.load_organizations()
        contact.refresh_from_db()
        organization = Organization.objects.first()
        self.assertEqual(organization.primary_contacts.count(), 1)
        self.assertEqual(organization.secondary_contacts.count(), 0)
        self.assertEqual(organization.primary_contacts.first(), contact)
        self.assertEqual(contact.organization, organization)

    def test_match_case_insensitive(self):
        contact = Contact.objects.create(
            organization=None,
            first_name="Zephyr",
            last_name="Moonweaver",
            emails=["ZePhyr.M@example.com", "another@uninteresting.org"],
        )
        self.load_organizations()
        contact.refresh_from_db()
        organization = Organization.objects.first()
        self.assertEqual(organization.primary_contacts.count(), 1)
        self.assertEqual(organization.secondary_contacts.count(), 0)
        self.assertEqual(organization.primary_contacts.first(), contact)
        self.assertEqual(contact.organization, organization)

    def test_primary_contacts_added_from_ccs(self):
        contact = Contact.objects.create(
            organization=None,
            first_name="Zephyr",
            last_name="Moonweaver",
            emails=["some@primary.email"],
            email_ccs=["zephyr.m@example.com", "another@uninteresting.org"],
        )
        self.load_organizations()
        contact.refresh_from_db()
        organization = Organization.objects.first()
        self.assertEqual(organization.primary_contacts.count(), 1)
        self.assertEqual(organization.secondary_contacts.count(), 0)
        self.assertEqual(organization.primary_contacts.first(), contact)
        self.assertEqual(contact.organization, organization)

    def test_primary_secondary_overlap(self):
        # If both org primary and secondary emails found, add as primary
        contact = Contact.objects.create(
            organization=None,
            first_name="Zephyr",
            last_name="Moonweaver",
            emails=["zephyr.m@example.com", "fly.away@zephyr.song"],
            email_ccs=["zephyr.m@example.com", "another@uninteresting.org"],
        )
        self.load_organizations()
        contact.refresh_from_db()
        organization = Organization.objects.first()
        self.assertEqual(organization.primary_contacts.count(), 1)
        self.assertEqual(organization.secondary_contacts.count(), 0)
        self.assertEqual(organization.primary_contacts.first(), contact)
        self.assertEqual(contact.organization, organization)

    def test_secondary_contacts_added(self):
        contact = Contact.objects.create(
            organization=None,
            first_name="Zephyr",
            last_name="Moonweaver",
            emails=["fly.away@zephyr.song"],
            email_ccs=["another@uninteresting.org"],
        )
        self.load_organizations()
        contact.refresh_from_db()
        organization = Organization.objects.first()
        self.assertEqual(organization.primary_contacts.count(), 0)
        self.assertEqual(organization.secondary_contacts.count(), 1)
        self.assertEqual(organization.secondary_contacts.first(), contact)
        self.assertEqual(contact.organization, organization)
