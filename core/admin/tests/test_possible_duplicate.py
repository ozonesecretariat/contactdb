from django.test import TestCase

from api.tests.factories import ContactFactory
from core.models import Contact, Organization, PossibleDuplicateContact


class TestPossibleDuplicate(TestCase):
    fixtures = [
        "initial/region",
        "initial/subregion",
        "initial/country",
        "initial/organizationtype",
        "test/organization",
    ]

    def setUp(self):
        organization = Organization.objects.first()
        ContactFactory(
            organization=organization,
            first_name="Jane",
            last_name="Eyre",
            emails=["janeeyre@gmail.com", "JaneEyre@gmail.com"],
        )

    def test_contact_with_case_variant_emails_is_not_duplicate_of_itself(self):
        """
        A contact with multiple duplicate emails that differ only in
        capitalization should not be considered a duplicate of itself.
        """
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(PossibleDuplicateContact.objects.count(), 0)
