from django.core.management import call_command
from django.test import TestCase

from core.models import Contact, Country, Organization, OrganizationType


class TestCleanOrganizationEmails(TestCase):
    fixtures = [
        "initial/country",
        "initial/organizationtype",
    ]

    def setUp(self):
        self.organization = Organization.objects.create(
            **{
                "name": "Intergalactic Defense Coalition",
                "acronym": "IDC",
                "organization_type": OrganizationType.objects.first(),
                "government": Country.objects.first(),
                "country": Country.objects.first(),
            }
        )

        self.organization.emails = [
            "janeyre@book.com",
            "dune@book.com",
            "essaysinlove@book.com",
        ]
        self.organization.email_ccs = [
            "janeyre@book.net",
            "dune@book.net",
            "essaysinlove@book.net",
        ]

        contact1 = Contact.objects.create(
            first_name="Jane",
            last_name="Roe",
            organization=self.organization,
            emails=["janeyre@book.com"],
            email_ccs=["janeyre@book.net"],
            country=Country.objects.first(),
        )

        contact2 = Contact.objects.create(
            first_name="Dune",
            last_name="Atreides",
            organization=self.organization,
            emails=["dune@book.com"],
            email_ccs=["dune@book.net"],
            country=Country.objects.first(),
        )

        self.organization.primary_contacts.add(contact1)
        self.organization.secondary_contacts.add(contact2)
        self.organization.save()

    def test_clean_organization_emails(self):
        call_command("clean_organization_emails")
        self.organization.refresh_from_db()

        self.assertEqual(
            self.organization.emails,
            ["essaysinlove@book.com"],
        )

        self.assertEqual(self.organization.email_ccs, ["essaysinlove@book.net"])
