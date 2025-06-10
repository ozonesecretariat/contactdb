from django.test import TestCase

from core.admin.contact_base import MergeContacts
from core.models import Contact, Country, Organization
from events.models import Event, Registration, RegistrationRole, RegistrationStatus


class TestMergeContactFk(TestCase):
    fixtures = [
        "test/event",
        "initial/country",
        "initial/organizationtype",
        "test/organization",
        "initial/registrationstatus",
        "initial/registrationrole",
    ]

    def setUp(self):
        self.event = Event.objects.all()[0]
        self.other_event = Event.objects.all()[1]
        self.organization = Organization.objects.first()
        self.country = Country.objects.first()
        registered = RegistrationStatus.objects.get(name="Registered")
        accredited = RegistrationStatus.objects.get(name="Accredited")
        role = RegistrationRole.objects.first()

        self.contact1 = Contact.objects.create(
            first_name="Jane",
            last_name="Eyre",
            organization=self.organization,
            emails=["janeyre@book.com"],
            email_ccs=["janeyre@book.net"],
            country=self.country,
        )

        self.contact2 = Contact.objects.create(
            first_name="Paul",
            last_name="Atreides",
            organization=self.organization,
            emails=["dune@book.com"],
            email_ccs=["dune@book.net"],
            country=self.country,
        )

        self.contact1.registrations.create(
            event=self.event,
            role=role,
            status=accredited,
            date="2023-09-01T12:00:00Z",
            is_funded=True,
        )
        self.contact2.registrations.create(
            event=self.event,
            role=role,
            status=registered,
            date="2023-10-02T12:00:00Z",
            is_funded=True,
        )
        self.contact2.registrations.create(
            event=self.other_event,
            role=role,
            status=accredited,
            date="2025-09-02T12:00:00Z",
            is_funded=True,
        )

    def test_merge_registrations(self):
        """
        Test that merging contacts keeps only the most recent
        registration for each event.
        """
        self.assertEqual(self.contact1.registrations.count(), 1)
        self.assertEqual(self.contact2.registrations.count(), 2)
        MergeContacts.merge_two_contacts(self.contact1, self.contact2)

        self.contact1.refresh_from_db()
        self.assertEqual(self.contact1.registrations.count(), 2)
        self.assertTrue(self.contact1.registrations.filter(event=self.event).exists())
        self.assertTrue(
            self.contact1.registrations.filter(event=self.other_event).exists()
        )

        # The conflicting contact should be deleted
        self.assertFalse(Contact.objects.filter(pk=self.contact2.pk).exists())
        self.assertEqual(Registration.objects.count(), 2)

        event_registration = self.contact1.registrations.filter(
            event=self.event
        ).first()
        self.assertEqual(
            event_registration.status.name,
            "Registered",
        )
