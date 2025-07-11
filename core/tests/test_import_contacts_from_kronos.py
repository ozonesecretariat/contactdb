import datetime
from copy import deepcopy
from unittest.mock import patch

from django.test import TestCase

from core.models import (
    Contact,
    Country,
    Organization,
    OrganizationType,
)
from core.parsers import ContactParser
from events.models import Event, RegistrationRole


class TestImportContactFromKronos(TestCase):
    fixtures = [
        "initial/region",
        "initial/subregion",
        "initial/country",
        "initial/organizationtype",
        "initial/registrationrole",
        "initial/registrationtag",
    ]

    def setUp(self):
        self.event = Event.objects.create(
            event_id="eventid",
            title="Quantum Quest: A Science Adventure Symposium",
            code="POM-2023",
            start_date="2023-01-01T00:00:00Z",
            end_date="2023-01-05T00:00:00Z",
            dates="1 - 5 January 2023",
        )

        self.organization = Organization.objects.create(
            name="Literary Society",
            organization_id="orgid",
            acronym="LS",
            country=Country.objects.get(code="GB"),
            government=Country.objects.get(code="GB"),
            organization_type=OrganizationType.objects.get(acronym="GOV"),
        )

        self.fake_contact = {
            "contactId": "contactid",
            "organizationId": "orgid",
            "organizationType": "GOV",
            "title": "Ms.",
            "firstName": "Jane",
            "lastName": "Eyre",
            "designation": "Expert",
            "department": "Environment and Energy",
            "affiliation": "Literary Society",
            "phones": ["+4999999999"],
            "mobiles": ["+4999999999"],
            "faxes": ["+4999999999"],
            "emails": ["jane@book.com"],
            "emailCcs": ["jane@book.net"],
            "notes": "I would always rather be happy than dignified. ##F, ##A, ##S",
            "isInMailingList": False,
            "isUseOrganizationAddress": True,
            "address": "Thornfield Hall, main road",
            "city": "Thornfield Hall",
            "state": "Hallshire",
            "country": "gb",
            "postalCode": "01234",
            "createdOn": "2015-05-08T12:03:31.019Z",
            "createdBy": "Charlotte Brontë",
            "updatedOn": "2025-06-08T14:03:21.019Z",
            "updatedBy": "Charlotte Brontë",
            "dateOfBirth": "1847-10-19",
        }

        self.fake_registration = [
            {
                "registrationId": "regid",
                "eventId": "eventid",
                "event": {
                    "eventId": "eventid",
                    "code": "POM-2023",
                    "title": "First Meeting of the Ladies in Blue Pants",
                    "startDate": "2023-01-01T00:00:00Z",
                    "endDate": "2023-01-05T00:00:00Z",
                    "venueCountry": "ec",
                    "venueCity": "Quito",
                    "dates": "1 - 5 January 2023",
                    "isOpenForRegistration": True,
                },
                "nominatedOn": "2022-12-01T10:00:00Z",
                "nominatedBy": "Charlotte Brontë",
                "accreditedOn": "2022-12-15T10:00:00Z",
                "accreditedBy": "Charlotte Brontë",
                "registeredOn": "2023-01-01T10:00:00Z",
                "registeredBy": "Charlotte Brontë",
                "isFunded": False,
                "isVisaRequired": False,
                "position": 5,
                "role": 1,
                "status": 4,
                "dynamicTags": [
                    "EVENT:00000000000000000004",
                    "CONTACT:00000000000000000001",
                    "TYPE:GOV",
                    "PARTY:TRUE",
                    "PARTY_TO:XXVII1",
                    "REGION:AFRICA",
                    "GROUP:AFRICA",
                ],
                "priorityPass": "LETMEIN",
                "priorityPassCode": "LETMEIN",
                "priorityPassGeneratedOn": "2022-12-20T10:00:00Z",
                "priorityPassSentOn": "2022-12-20T10:00:00Z",
                "priorityPassSentTo": "jane@book.com",
                "priorityPassUrl": "www.example.com/priority_pass.pdf",
                "passportCount": 0,
                "contactId": "contactid",
                "organizationId": "orgid",
                "organizationType": "GOV",
                "title": "Mr.",
                "firstName": "Jane",
                "lastName": "Eyre",
                "designation": "Expert",
                "department": "Environment and Energy",
                "affiliation": "Literary Society",
                "phones": ["+4999999999"],
                "mobiles": ["+4999999999"],
                "faxes": ["+4999999999"],
                "emails": ["jane@book.com"],
                "emailCcs": ["jane@book.com"],
                "notes": "I would always rather be happy than dignified. ##F, ##A, ##S",
                "isInMailingList": False,
                "isUseOrganizationAddress": True,
                "address": "Thornfield Hall, main road",
                "city": "Thornfield Hall",
                "state": "Hallshire",
                "country": "gb",
                "postalCode": "01234",
                "createdOn": "2015-05-08T12:03:31.019Z",
                "createdBy": "Charlotte Brontë",
                "updatedOn": "2025-06-08T14:03:21.019Z",
                "updatedBy": "Charlotte Brontë",
            }
        ]

        self.mock_client = patch("core.parsers.KronosClient").start()
        self.mock_client.return_value.get_contact_data.side_effect = (
            lambda *args: deepcopy(self.fake_contact)
        )

        self.mock_client.return_value.get_registrations_data.side_effect = (
            lambda *args: deepcopy(self.fake_registration)
        )

    def tearDown(self):
        patch.stopall()

    def test_import_contact_from_kronos(self):
        parser = ContactParser()

        parser.import_contacts_with_registrations(
            [self.fake_contact["contactId"]],
        )

        self.assertEqual(Contact.objects.count(), 1)
        contact = Contact.objects.first()

        self.assertEqual(contact.contact_ids, ["contactid"])
        self.assertIsNotNone(contact.organization)
        self.assertEqual(contact.organization.name, "Literary Society")
        self.assertEqual(contact.organization.organization_id, "orgid")
        self.assertIsNotNone(contact.country)

        self.assertEqual(contact.title, "Ms.")
        self.assertEqual(contact.first_name, "Jane")
        self.assertEqual(contact.last_name, "Eyre")
        self.assertEqual(contact.designation, "Expert")
        self.assertEqual(contact.department, "Environment and Energy")
        self.assertEqual(contact.affiliation, "Literary Society")
        self.assertEqual(contact.phones, ["+4999999999"])
        self.assertEqual(contact.mobiles, ["+4999999999"])
        self.assertEqual(contact.faxes, ["+4999999999"])
        self.assertEqual(contact.emails, ["jane@book.com"])
        self.assertEqual(contact.email_ccs, ["jane@book.net"])
        self.assertEqual(
            contact.notes,
            "I would always rather be happy than dignified. ##F, ##A, ##S",
        )
        self.assertEqual(contact.is_use_organization_address, True)
        self.assertEqual(contact.address, "Thornfield Hall, main road")
        self.assertEqual(contact.city, "Thornfield Hall")
        self.assertEqual(contact.state, "Hallshire")
        self.assertEqual(contact.postal_code, "01234")
        self.assertEqual(
            contact.birth_date, datetime.datetime.fromisoformat("1847-10-19").date()
        )
        self.assertEqual(contact.primary_lang, "F")
        self.assertEqual(contact.second_lang, "A")
        self.assertEqual(contact.third_lang, "S")

        self.assertEqual(contact.registrations.count(), 1)
        registration = contact.registrations.first()
        self.assertEqual(registration.event, self.event)
        self.assertEqual(registration.contact, contact)
        self.assertEqual(registration.status, "Registered")
        self.assertEqual(registration.priority_pass_code, "LETMEIN")
        self.assertEqual(
            registration.date,
            datetime.datetime(
                2015, 5, 8, 12, 3, 31, 19000, tzinfo=datetime.timezone.utc
            ),
        )
        self.assertEqual(registration.is_funded, False)
        self.assertEqual(
            registration.role, RegistrationRole.objects.get(name="Alternate Head")
        )
