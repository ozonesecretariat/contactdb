from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase
from core.models import Contact, ContactGroup, Country, Organization


class TestImportFocalPoints(TestCase):
    fixtures = [
        "initial/contactgroup",
        "initial/country",
    ]

    def setUp(self):
        self.fake_item = {
            "id": 123,
            "party": " \t Portugal ",
            "name": "Mr. Johnny Doe \t",
            "designation": "Janitor",
            "tel": "(+00) 1234 5678   ",
            "email": "johnny.doe1@example.com    ;  \t   johnny.doe2@example.com",
            "fax": "",
            "organisation": " Intergalactic Defense Coalition\t",
            "city": "Lisbon",
            "country": "Spain",
            "address": "Real Street 42",
            "is_licensing_system": False,
            "is_national": False,
            "ordering_id": -1,
        }
        self.mock_data = [self.fake_item]
        self.mock_request = patch("requests.get").start()
        self.mock_request.return_value.json.side_effect = lambda: self.mock_data

    def tearDown(self):
        patch.stopall()

    def test_import_focal_points(self):
        call_command("import_focal_points")

        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(Organization.objects.count(), 1)

        contact = Contact.objects.first()
        organization = Organization.objects.first()

        self.assertEqual(contact.focal_point_ids, [123])
        self.assertEqual(contact.title, "Mr.")
        self.assertEqual(contact.first_name, "Johnny")
        self.assertEqual(contact.last_name, "Doe")
        self.assertEqual(contact.designation, "Janitor")
        self.assertEqual(contact.organization, organization)
        self.assertEqual(contact.country.code, "PT")
        self.assertEqual(contact.address, "Real Street 42")
        self.assertEqual(
            contact.emails, ["johnny.doe1@example.com", "johnny.doe2@example.com"]
        )
        self.assertEqual(contact.phones, ["(+00) 1234 5678"])
        self.assertEqual(
            set(contact.groups.all()),
            {
                ContactGroup.objects.get(name="Focal point"),
            },
        )

        self.assertEqual(organization.name, "Intergalactic Defense Coalition")
        self.assertEqual(organization.country.code, "ES")
        self.assertEqual(organization.government.code, "PT")

    def test_skip_already_imported(self):
        call_command("import_focal_points")
        self.assertEqual(Contact.objects.count(), 1)
        call_command("import_focal_points")
        self.assertEqual(Contact.objects.count(), 1)

    def test_skip_already_imported_after_merge(self):
        call_command("import_focal_points")
        contact = Contact.objects.first()
        contact.focal_point_ids.extend([10, 11, 12])
        contact.save()

        call_command("import_focal_points")
        self.assertEqual(Contact.objects.count(), 1)

    def test_check_licensing_system(self):
        self.fake_item["is_licensing_system"] = True
        call_command("import_focal_points")
        contact = Contact.objects.first()
        self.assertEqual(
            set(contact.groups.all()),
            {
                ContactGroup.objects.get(name="Focal point"),
                ContactGroup.objects.get(name="FPLS"),
            },
        )

    def test_check_national(self):
        self.fake_item["is_national"] = True
        call_command("import_focal_points")
        contact = Contact.objects.first()
        self.assertEqual(
            set(contact.groups.all()),
            {
                ContactGroup.objects.get(name="Focal point"),
                ContactGroup.objects.get(name="NFP"),
            },
        )

    def test_check_fuzzy_country_match(self):
        # The full name is "United Kingdom of Great Britain and Northern Ireland".
        # But this should be enough to match it regardless.
        self.fake_item["party"] = "Great britain"
        call_command("import_focal_points")
        contact = Contact.objects.first()
        self.assertEqual(contact.country.code, "GB")

    def test_check_fuzzy_country_multi_match(self):
        # This case cannot be resolved with 100% accuracy since there are two
        # countries with similar names:
        #  - Congo, The Democratic Republic of the (CD)
        #  - Republic of the Congo (CG)
        self.fake_item["party"] = "republic of congo"
        call_command("import_focal_points")
        self.assertEqual(Contact.objects.count(), 0)

    def test_check_fuzzy_country_no_match(self):
        self.fake_item["party"] = "Hallownest"
        call_command("import_focal_points")
        self.assertEqual(Contact.objects.count(), 0)

    def test_check_organization_match_name(self):
        org = Organization.objects.create(name="Intergalactic Defense Coalition")
        call_command("import_focal_points")
        contact = Contact.objects.first()
        self.assertEqual(contact.organization, org)

    def test_check_organization_match_alt_names(self):
        org = Organization.objects.create(
            name="Int. Defense Coalition",
            alt_names=[
                "Intergalactic Defense Alliance",
                "intergalactic defense coalition",
            ],
        )
        call_command("import_focal_points")
        contact = Contact.objects.first()
        self.assertEqual(contact.organization, org)

    def test_check_organization_fuzzy_match(self):
        org = Organization.objects.create(
            name="Int. Defense Coalition",
            country=Country.objects.get(code="PT"),
        )
        call_command("import_focal_points")
        contact = Contact.objects.first()
        self.assertEqual(contact.organization, org)

    def test_check_organization_multi_match(self):
        org1 = Organization.objects.create(
            name="Int. Defense Coalition",
            country=Country.objects.get(code="PT"),
        )
        org2 = Organization.objects.create(
            name="Int Defense Coalition",
            country=Country.objects.get(code="PT"),
        )
        call_command("import_focal_points")
        contact = Contact.objects.first()
        # There are two valid matches, so instead we create a third organization
        self.assertNotEqual(contact.organization, org1)
        self.assertNotEqual(contact.organization, org2)
        self.assertEqual(
            contact.organization.name,
            "Intergalactic Defense Coalition",
        )
