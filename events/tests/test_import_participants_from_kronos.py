from copy import deepcopy
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from core.models import Contact, Organization, OrganizationType, ResolveConflict
from events.models import Event, LoadParticipantsFromKronosTask


class TestImportEvents(TestCase):
    fixtures = [
        "initial/country",
        "initial/organizationtype",
        "initial/registrationrole",
        "initial/registrationstatus",
        "initial/registrationtag",
    ]

    def setUp(self):
        self.gov_id = OrganizationType.objects.get(acronym="GOV").organization_type_id
        self.biz_id = OrganizationType.objects.get(acronym="BIZ").organization_type_id

        self.event = Event.objects.create(
            event_id="abc",
            title="Quantum Quest: A Science Adventure Symposium",
            code="QQ:ASAA",
            start_date="2010-07-1T00:00:00Z",
            end_date="2010-07-10T00:00:00Z",
            dates="1-10 July 2010",
        )
        self.fake_item = {
            "address": "1234 Giggleberry Lane, Fluffytown, Fantasia 98765",
            "affiliation": "",
            "city": "Luanda",
            "contactId": "99999999999999",
            "country": "ao",
            "createdBy": "Zephyr McFluffernutter",
            "createdOn": "2015-07-03T00:00:00.000Z",
            "department": (
                "The Department of Quantum Agriculture and Temporal Horticulture"
            ),
            "designation": "Chief Synergy Architect",
            "emailCcs": [],
            "emails": ["zephyr.m@example.com"],
            "faxes": ["+999999999"],
            "firstName": "Nimbus",
            "isInMailingList": False,
            "isUseOrganizationAddress": True,
            "lastName": "Fizzlepop-Wobblebottom",
            "mobiles": ["+88888888"],
            "notes": "",
            "organization": {
                "acronym": "",
                "country": "ao",
                "countryName": "Angola",
                "government": "pl",
                "governmentName": "Poland",
                "name": "The Society of Whimsical Antics and Nonsensical Endeavors",
                "organizationId": "11111111111",
                "organizationType": "GOV",
                "organizationTypeId": self.gov_id,
            },
            "organizationId": "11111111111",
            "organizationType": "GOV",
            "phones": ["+777777777"],
            "postalCode": "",
            "registrationStatuses": [
                {
                    "code": "QQ:ASAA",
                    "date": "2010-10-2T10:00:00.000Z",
                    "eventId": "abc",
                    "isFunded": False,
                    "status": 1,
                }
            ],
            "state": "",
            "title": "Ms.",
            "updatedBy": "Snickerdoodle Wobblepants",
            "updatedOn": "2010-01-00T00:00:00.000Z",
        }

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
            "emailCcs": [],
            "webs": [],
            "notes": "",
            "isCheckNotes": False,
            "isValidated": False,
            "validatedBy": "Unknown",
            "validations": [],
            "isDateOfBirthRequired": False,
            "isHidden": False,
            "isInMailingList": False,
            "createdOn": "2017-07-03T09:15:31.036Z",
            "createdBy": "",
            "updatedOn": "2025-03-07T08:38:18.875Z",
            "updatedBy": "",
        }

        self.mock_data = [self.fake_item]
        self.mock_client = patch("events.parsers.KronosClient").start()
        self.mock_client.return_value.get_participants.side_effect = (
            lambda *args: deepcopy(self.mock_data)
        )

        self.mock_client.return_value.get_organizations_for_event.side_effect = (
            lambda *args: [self.fake_org]
        )

    def tearDown(self):
        patch.stopall()

    def load_participants(self):
        LoadParticipantsFromKronosTask.objects.create(event=self.event).run(
            is_async=False
        )

    def test_load_participant(self):
        self.load_participants()

        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(Organization.objects.count(), 1)
        contact = Contact.objects.first()
        organization = Organization.objects.first()

        self.assertEqual(contact.country.name, "Angola")
        self.assertEqual(contact.organization, organization)
        self.assertEqual(contact.full_name, "Ms. Nimbus Fizzlepop-Wobblebottom")
        self.assertEqual(contact.emails, ["zephyr.m@example.com"])
        self.assertEqual(contact.phones, ["+777777777"])
        self.assertEqual(contact.registrations.count(), 1)
        self.assertEqual(contact.registrations.first().event, self.event)

        self.assertEqual(
            organization.name,
            "The Society of Whimsical Antics and Nonsensical Endeavors",
        )
        self.assertEqual(organization.country.name, "Angola")
        self.assertEqual(organization.government.name, "Poland")
        self.assertEqual(organization.address, "real place")
        self.assertEqual(organization.postal_code, "123456789")
        self.assertEqual(organization.emails, ["zephyr.m@example.com"])

        self.assertEqual(organization.primary_contacts.count(), 1)
        self.assertEqual(organization.primary_contacts.first(), contact)
        # Gob without #invite in notes
        self.assertEqual(organization.include_in_invitation, False)

    def test_load_gov_with_invite(self):
        self.fake_org["notes"] = "something #invite"
        self.load_participants()
        organization = Organization.objects.first()
        self.assertEqual(organization.include_in_invitation, True)

    def test_load_non_gov_old(self):
        self.fake_org["organizationTypeId"] = self.biz_id
        self.load_participants()
        organization = Organization.objects.first()
        self.assertEqual(organization.include_in_invitation, False)

    def test_load_non_gov_new(self):
        self.event.start_date = timezone.now()
        self.event.end_date = timezone.now()
        self.event.save()

        self.fake_org["organizationTypeId"] = self.biz_id
        self.load_participants()
        organization = Organization.objects.first()
        self.assertEqual(organization.include_in_invitation, True)

    def test_match_case_insensitive(self):
        self.fake_org["emails"][0] = self.fake_org["emails"][0].upper()
        self.load_participants()
        organization = Organization.objects.first()
        self.assertEqual(organization.primary_contacts.count(), 1)

    def test_load_participant_conflict(self):
        self.load_participants()

        # Change something in the contact
        self.assertEqual(Contact.objects.count(), 1)
        contact = Contact.objects.first()
        contact.title = "Mr."
        contact.save()

        # Load again
        self.load_participants()
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(ResolveConflict.objects.count(), 1)

        conflict = ResolveConflict.objects.first()
        self.assertEqual(conflict.existing_contact, contact)
        self.assertEqual(conflict.title, "Ms.")

        # Load again to check a duplicate conflict is NOT created
        self.load_participants()
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(ResolveConflict.objects.count(), 1)
