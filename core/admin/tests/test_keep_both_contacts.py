from copy import deepcopy
from unittest.mock import patch

from django.urls import reverse

from api.tests.base import BaseAPITestCase
from api.tests.factories import (
    ContactFactory,
    EventFactory,
    OrganizationFactory,
    RegistrationFactory,
    ResolveConflictFactory,
)
from core.models import (
    Contact,
    ResolveConflict,
)
from events.models import Registration


class TestKeepBothContacts(BaseAPITestCase):
    url = "/admin/core/resolveconflict/"
    fixtures = [
        "initial/role",
        "test/user",
        "initial/region",
        "initial/subregion",
        "initial/country",
        "initial/organizationtype",
        "initial/registrationtag",
    ]

    def setUp(self):
        self.event = EventFactory(event_id="eventid")
        self.organization = OrganizationFactory(organization_id="orgid")
        self.contact = ContactFactory(
            emails=["jane@book.com"], first_name="Main Contact"
        )
        self.conflict1 = ResolveConflictFactory(
            first_name="Conflict1",
            emails=["jane@book.com"],
            existing_contact=self.contact,
        )
        self.conflict2 = ResolveConflictFactory(
            emails=["jane@book.com"],
            first_name="Conflict2",
            existing_contact=self.contact,
        )

        self.registration = RegistrationFactory(contact=self.contact, event=self.event)

        def get_contact_data_side_effect(contact_id, *args, **kwargs):
            if contact_id == "contactid1":
                return deepcopy(self.fake_contact1)
            if contact_id == "contactid2":
                return deepcopy(self.fake_contact2)

            return None

        def get_registration_data_side_effect(contact_id, *args, **kwargs):
            if contact_id == "contactid1":
                return deepcopy(self.fake_registration)
            return None

        self.mock_client = patch("core.parsers.KronosClient").start()
        self.mock_client.return_value.get_contact_data.side_effect = (
            get_contact_data_side_effect
        )

        self.mock_client.return_value.get_registrations_data.side_effect = (
            get_registration_data_side_effect
        )

        self.fake_contact1 = {
            "contactId": "contactid1",
            "organizationId": "orgid",
            "organizationType": "GOV",
            "title": "H.E. Sr.",
            "firstName": "Jane",
            "lastName": "Eyre",
            "designation": "Expert",
            "department": "Environment and Energy",
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

        self.fake_contact2 = {
            "contactId": "contactid2",
            "organizationId": "orgid",
            "organizationType": "GOV",
            "title": "H.E. Sra.",
            "firstName": "Jane",
            "lastName": "Eyre",
            "designation": "Expert",
            "department": "Environment and Energy",
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

    def tearDown(self):
        patch.stopall()

    def test_keep_both_local_contacts(self):
        """
        Test that keeping both contacts works with local contacts
        (contacts that were not imported from Kronos).
        """
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(ResolveConflict.objects.count(), 2)
        self.assertEqual(Registration.objects.count(), 1)
        self.assertEqual(self.contact.registrations.count(), 1)

        self.login_admin()
        url = reverse("admin:core_resolveconflict_changelist")
        data = {
            "action": "keep_both_contacts",
            "select_across": "0",
            "index": "0",
            "_selected_action": self.conflict1.pk,
        }
        response = self.client.post(
            path=url,
            data=data,
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Contact.objects.count(), 2)
        self.assertEqual(ResolveConflict.objects.count(), 1)
        self.assertEqual(ResolveConflict.objects.first().first_name, "Conflict2")

        self.mock_client.return_value.get_contact_data.assert_not_called()
        self.mock_client.return_value.get_registrations_data.assert_not_called()

    def test_keep_both_kronos_contacts(self):
        """
        Test that `keep both contacts` works with Kronos contacts.
        All contact_ids of the main contact will be reimported, all
        conflicts will be made into new contacts.
        """
        self.contact.contact_ids = ["contactid1", "contactid2"]
        self.contact.save()

        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(ResolveConflict.objects.count(), 2)
        self.assertEqual(Registration.objects.count(), 1)

        self.login_admin()
        url = reverse("admin:core_resolveconflict_changelist")
        data = {
            "action": "keep_both_contacts",
            "select_across": "0",
            "index": "0",
            "_selected_action": self.conflict1.pk,
        }
        response = self.client.post(
            path=url,
            data=data,
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Contact.objects.count(), 4)
        self.assertEqual(ResolveConflict.objects.count(), 0)
        self.assertEqual(Registration.objects.count(), 1)

        imported_contacts = Contact.objects.filter(contact_ids__isnull=False)
        self.assertEqual(imported_contacts.count(), 2)

        contact1 = Contact.objects.get(contact_ids=["contactid1"])
        contact2 = Contact.objects.get(contact_ids=["contactid2"])

        self.assertEqual(contact1.registrations.count(), 1)

        self.assertEqual(contact1.title, "H.E. Mr.")
        self.assertEqual(contact1.title_localized, "H.E. Sr.")
        self.assertEqual(contact2.title, "H.E. Ms.")
        self.assertEqual(contact2.title_localized, "H.E. Sra.")
        self.assertEqual(contact1.registrations.count(), 1)

        self.assertEqual(Contact.objects.filter(contact_ids__isnull=True).count(), 2)

    def test_keep_both_mixed_contacts(self):
        """
        Test that keep both contacts works with a mix of local and
        Kronos contacts.
        """
        self.contact.contact_ids = ["contactid1"]
        self.contact.save()

        local_contact = ContactFactory(
            first_name="Other contact",
            emails=["jane@book.com"],
        )
        self.conflict2.existing_contact = local_contact
        self.conflict2.save()

        self.assertEqual(Contact.objects.count(), 2)
        self.assertEqual(ResolveConflict.objects.count(), 2)
        self.assertEqual(Registration.objects.count(), 1)

        self.login_admin()
        url = reverse("admin:core_resolveconflict_changelist")
        data = {
            "action": "keep_both_contacts",
            "select_across": "0",
            "index": "0",
            "_selected_action": [self.conflict1.pk, self.conflict2.pk],
        }
        response = self.client.post(
            path=url,
            data=data,
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Contact.objects.count(), 4)
        self.assertEqual(ResolveConflict.objects.count(), 0)
        self.assertEqual(Registration.objects.count(), 1)

        contact1 = Contact.objects.get(contact_ids=["contactid1"])
        self.assertEqual(contact1.first_name, "Jane")
        self.assertEqual(contact1.registrations.count(), 1)

        self.assertEqual(Contact.objects.filter(contact_ids__isnull=True).count(), 3)
