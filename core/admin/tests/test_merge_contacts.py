from datetime import UTC, datetime

from django.test import TestCase

from core.admin.contact_base import MergeContacts
from core.models import Contact, ContactGroup, Country, Organization, ResolveConflict
from events.models import Event, Registration, RegistrationRole


class TestMergeContacts(TestCase):
    fixtures = [
        "initial/contactgroup",
        "test/eventgroup",
        "test/event",
        "initial/country",
        "initial/organizationtype",
        "test/organization",
        "initial/registrationrole",
    ]

    def setUp(self):
        events = Event.objects.all()
        self.event = events[0]
        self.other_event = events[1]

        orgs = Organization.objects.all()
        self.org1 = orgs[0]
        self.org2 = orgs[1]

        countries = Country.objects.all()
        self.country1 = countries[0]
        self.country2 = countries[1]

        roles = RegistrationRole.objects.all()
        self.role1 = roles[0]
        self.role2 = roles[1]

        self.registered = Registration.Status.REGISTERED
        self.accredited = Registration.Status.ACCREDITED

        self.contact1 = Contact.objects.create(
            title="Ms.1",
            honorific="Miss 1",
            first_name="Jane 1",
            last_name="Eyre 1",
            country=self.country1,
            emails=["janeeyre1@book.com"],
            email_ccs=["janeeyre1@book.net"],
            phones=["1000000000"],
            mobiles=["1000000000"],
            faxes=["1000000000"],
            organization=self.org1,
            designation="State secretary 1",
            department="Department of State 1",
            org_head=True,
            is_use_organization_address=True,
            city="City 1",
            state="State 1",
            postal_code="111111",
            address="Address 1",
            primary_lang=Contact.UNLanguage.ENGLISH,
            second_lang=Contact.UNLanguage.FRENCH,
            third_lang=Contact.UNLanguage.SPANISH,
            birth_date=datetime(1992, 1, 1, tzinfo=UTC),
            notes="Notes 1",
            contact_ids=["111111"],
            focal_point_ids=["1"],
            photo_access_uuid=None,
        )

        self.contact2 = Contact.objects.create(
            title="Ms.2",
            honorific="Miss 2",
            first_name="Jane 2",
            last_name="Eyre 2",
            country=self.country2,
            emails=["janeeyre2@book.com"],
            email_ccs=["janeeyre2@book.net"],
            phones=["2000000000"],
            mobiles=["2000000000"],
            faxes=["2000000000"],
            organization=self.org2,
            designation="State secretary 2",
            department="Department of State 2",
            org_head=False,
            is_use_organization_address=False,
            city="City 2",
            state="State 2",
            postal_code="2",
            address="Address 2",
            primary_lang=Contact.UNLanguage.SPANISH,
            second_lang=Contact.UNLanguage.ARABIC,
            third_lang=Contact.UNLanguage.CHINESE,
            birth_date=datetime(1992, 2, 2, tzinfo=UTC),
            notes="Notes 2",
            contact_ids=["2"],
            focal_point_ids=["2"],
            photo_access_uuid=None,
        )

        self.contact1.registrations.create(
            event=self.event,
            role=self.role1,
            status=self.accredited,
            date=datetime(2023, 9, 1, tzinfo=UTC),
            is_funded=True,
        )

        self.contact2.registrations.create(
            event=self.other_event,
            role=self.role2,
            status=self.accredited,
            date=datetime(2023, 9, 2, tzinfo=UTC),
            is_funded=True,
        )

        groups = ContactGroup.objects.all()
        self.group1 = groups[0]
        self.group2 = groups[1]

        self.contact1.groups.add(self.group1)
        self.contact2.groups.add(self.group2)

    def test_merge_contacts(self):
        """
        Test merging contacts behaviour.
        """
        self.assertEqual(Contact.objects.count(), 2)
        self.assertEqual(self.contact1.registrations.count(), 1)
        self.assertEqual(self.contact2.registrations.count(), 1)
        conflict = MergeContacts.merge_two_contacts(self.contact1, self.contact2)

        # Contact 1 remains unchanged except for array fields and
        # relation fields which are extended with data from Contact 2.
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(ResolveConflict.objects.count(), 1)
        self.assertEqual(self.contact1.title, "Ms.1")
        self.assertEqual(self.contact1.honorific, "Miss 1")
        self.assertEqual(self.contact1.first_name, "Jane 1")
        self.assertEqual(self.contact1.last_name, "Eyre 1")
        self.assertEqual(self.contact1.country, self.country1)
        self.assertEqual(
            self.contact1.emails, ["janeeyre1@book.com", "janeeyre2@book.com"]
        )
        self.assertEqual(
            self.contact1.email_ccs, ["janeeyre1@book.net", "janeeyre2@book.net"]
        )
        self.assertEqual(self.contact1.phones, ["1000000000", "2000000000"])
        self.assertEqual(self.contact1.mobiles, ["1000000000", "2000000000"])
        self.assertEqual(self.contact1.faxes, ["1000000000", "2000000000"])
        self.assertEqual(self.contact1.organization, self.org1)
        self.assertEqual(self.contact1.designation, "State secretary 1")
        self.assertEqual(self.contact1.department, "Department of State 1")
        self.assertTrue(self.contact1.org_head)
        self.assertTrue(self.contact1.is_use_organization_address)
        self.assertEqual(self.contact1.city, "City 1")
        self.assertEqual(self.contact1.state, "State 1")
        self.assertEqual(self.contact1.postal_code, "111111")
        self.assertEqual(self.contact1.address, "Address 1")
        self.assertEqual(self.contact1.primary_lang, Contact.UNLanguage.ENGLISH)
        self.assertEqual(self.contact1.second_lang, Contact.UNLanguage.FRENCH)
        self.assertEqual(self.contact1.third_lang, Contact.UNLanguage.SPANISH)
        self.assertEqual(self.contact1.birth_date, datetime(1992, 1, 1, tzinfo=UTC))
        self.assertEqual(self.contact1.notes, "Notes 1")
        self.assertEqual(self.contact1.contact_ids, ["111111", "2"])
        self.assertEqual(self.contact1.focal_point_ids, ["1", "2"])
        self.assertEqual(self.contact1.registrations.count(), 2)
        self.assertEqual(self.contact1.groups.count(), 2)

        # ResolveConflict object is created with contact2's data,
        # except for array, relations, ignored fields.
        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.title, "Ms.2")
        self.assertEqual(conflict.honorific, "Miss 2")
        self.assertEqual(conflict.first_name, "Jane 2")
        self.assertEqual(conflict.last_name, "Eyre 2")
        self.assertEqual(conflict.country, self.country2)
        self.assertEqual(conflict.emails, [])
        self.assertEqual(conflict.email_ccs, [])
        self.assertEqual(conflict.phones, [])
        self.assertEqual(conflict.mobiles, [])
        self.assertEqual(conflict.faxes, [])
        self.assertEqual(conflict.organization, self.org2)
        self.assertEqual(conflict.designation, "State secretary 2")
        self.assertEqual(conflict.department, "Department of State 2")
        self.assertFalse(conflict.org_head)
        self.assertFalse(conflict.is_use_organization_address)
        self.assertEqual(conflict.city, "City 2")
        self.assertEqual(conflict.state, "State 2")
        self.assertEqual(conflict.postal_code, "2")
        self.assertEqual(conflict.address, "Address 2")
        self.assertEqual(conflict.primary_lang, Contact.UNLanguage.SPANISH)
        self.assertEqual(conflict.second_lang, Contact.UNLanguage.ARABIC)
        self.assertEqual(conflict.third_lang, Contact.UNLanguage.CHINESE)
        self.assertEqual(conflict.birth_date, datetime(1992, 2, 2, tzinfo=UTC))
        self.assertEqual(conflict.notes, "Notes 2")

        self.assertFalse(hasattr(conflict, "contact_ids"))
        self.assertFalse(hasattr(conflict, "focal_point_ids"))

    def test_merge_registrations(self):
        """
        Test that merging contacts keeps only the most recent
        registration for each event.
        """
        self.contact2.registrations.create(
            event=self.event,
            role=self.role2,
            status=self.registered,
            date=datetime(2023, 10, 2, tzinfo=UTC),
            is_funded=True,
        )

        self.assertEqual(self.contact1.registrations.count(), 1)
        self.assertEqual(self.contact2.registrations.count(), 2)
        MergeContacts.merge_two_contacts(self.contact1, self.contact2)

        self.contact1.refresh_from_db()
        self.assertEqual(self.contact1.registrations.count(), 2)
        self.assertTrue(self.contact1.registrations.filter(event=self.event).exists())
        self.assertTrue(
            self.contact1.registrations.filter(event=self.other_event).exists()
        )

        # Contact2 should be deleted
        self.assertFalse(Contact.objects.filter(pk=self.contact2.pk).exists())
        self.assertEqual(Registration.objects.count(), 2)

        event_registration = self.contact1.registrations.filter(
            event=self.event
        ).first()
        self.assertEqual(
            event_registration.status,
            Registration.Status.REGISTERED,
        )

    def test_merge_duplicate_contacts(self):
        """
        Test that merging contacts with the same data does not create a
        conflict. Only one contact is left in the database.
        """
        contact1_dict = Contact.objects.filter(id=self.contact1.id).values(
            "title",
            "first_name",
            "last_name",
            "designation",
            "department",
            "phones",
            "mobiles",
            "faxes",
            "emails",
            "email_ccs",
            "notes",
            "is_use_organization_address",
            "address",
            "city",
            "state",
            "postal_code",
            "country_id",
            "organization_id",
            "org_head",
            "photo_access_uuid",
        )[0]

        duplicate_contact = Contact.objects.create(
            **contact1_dict, birth_date=datetime(1992, 1, 1, tzinfo=UTC)
        )

        self.assertEqual(Contact.objects.count(), 3)

        conflict = MergeContacts.merge_two_contacts(self.contact1, duplicate_contact)
        self.assertIsNone(conflict)
        self.assertEqual(Contact.objects.count(), 2)
