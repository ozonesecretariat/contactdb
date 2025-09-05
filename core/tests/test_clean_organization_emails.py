from django.core.management import call_command
from django.test import TestCase

from core.models import Contact, Country, Organization, OrganizationType


class TestCleanOrganizationEmails(TestCase):
    fixtures = [
        "initial/region",
        "initial/subregion",
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

        self.primary_contact = Contact.objects.create(
            first_name="Jane",
            last_name="Roe",
            organization=self.organization,
            emails=["janeyre@book.com"],
            email_ccs=["janeyre@book.net"],
            country=Country.objects.first(),
        )

        self.secondary_contact = Contact.objects.create(
            first_name="Dune",
            last_name="Atreides",
            organization=self.organization,
            emails=["dune@book.com"],
            email_ccs=["dune@book.net"],
            country=Country.objects.first(),
        )

        self.organization.primary_contacts.add(self.primary_contact)
        self.organization.secondary_contacts.add(self.secondary_contact)
        self.organization.save()

    def test_clean_organization_emails(self):
        call_command("clean_organization_emails")
        self.organization.refresh_from_db()

        self.assertEqual(
            self.organization.emails,
            ["essaysinlove@book.com"],
        )

        self.assertEqual(self.organization.email_ccs, ["essaysinlove@book.net"])

    def test_clean_organization_emails_with_caps(self):
        """
        Test that emails are cleaned correctly even with different
        cases.
        """
        self.organization.emails.extend(["ciRce@book.com"])
        self.organization.email_ccs.append("ciRce@book.net")
        self.organization.save()

        self.primary_contact.emails.append("CIRCE@book.com")
        self.primary_contact.email_ccs.append("CIRCE@book.net")
        self.primary_contact.save()

        call_command("clean_organization_emails")
        self.organization.refresh_from_db()

        self.assertEqual(
            self.organization.emails,
            ["essaysinlove@book.com"],
        )
        self.assertEqual(self.organization.email_ccs, ["essaysinlove@book.net"])
