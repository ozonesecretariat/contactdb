import io

import docx
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from api.tests.factories import (
    ContactFactory,
    EventFactory,
    OrganizationFactory,
    RegistrationFactory,
)
from core.models import Country, OrganizationType
from events.models import Registration, RegistrationRole
from events.tests.utils import (
    extract_text_from_docx,
    extract_text_from_docx_footers,
    extract_text_from_docx_headers,
    get_table_data,
)


class TestListOfParticipants(TestCase):
    fixtures = [
        "initial/registrationrole",
        "initial/organizationtype",
        "initial/region",
        "initial/subregion",
        "initial/country",
        "initial/role",
        "test/user",
    ]

    ORG_TYPE = None

    def setUp(self):
        self.event = EventFactory()

        self.country1 = Country.objects.get(pk="RO")
        self.country2 = Country.objects.get(pk="ES")
        self.country3 = Country.objects.get(pk="FR")

        self.head = RegistrationRole.objects.get(name="Head")
        self.alt_head = RegistrationRole.objects.get(name="Alternate Head")

        self.gov = OrganizationType.objects.get(acronym="GOV")
        self.ass = OrganizationType.objects.get(acronym="ASS-PANEL")
        self.sec = OrganizationType.objects.get(acronym="SECRETARIAT")
        self.obs = OrganizationType.objects.get(acronym="OBS")
        self.biz = OrganizationType.objects.get(acronym="BIZ")

        self.org_type = OrganizationType.objects.get(acronym=self.ORG_TYPE)

        self.org1 = OrganizationFactory(
            government=self.country1, organization_type=self.org_type
        )
        self.org2 = OrganizationFactory(
            government=self.country1, organization_type=self.org_type
        )

        self.contact1 = ContactFactory(organization=self.org1, last_name="XXX")
        self.contact2 = ContactFactory(organization=self.org2, last_name="AAA")

        self.reg1 = RegistrationFactory(
            event=self.event,
            contact=self.contact1,
            organization=self.org1,
            status=Registration.Status.REGISTERED,
            role=self.head,
        )
        self.reg2 = RegistrationFactory(
            event=self.event,
            contact=self.contact2,
            organization=self.org2,
            status=Registration.Status.REGISTERED,
            role=self.alt_head,
        )

    def get_doc(self):
        url = reverse("admin:lop", args=(self.event.id,))
        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(url)
        f = io.BytesIO(b"".join(resp.streaming_content))
        return docx.Document(f)

    def check_doc(self, expected=None):
        result = get_table_data(self.get_doc())

        if expected is None:
            return result

        self.assertEqual(result.keys(), expected.keys())
        count = 0
        for name, expected_contacts in expected.items():
            self.assertIn(name, result)
            table = result[name]

            self.assertEqual(len(table), len(expected_contacts) + 1)
            for index, contact in enumerate(expected_contacts, start=1):
                count += 1
                global_index, contact_details = table[index]
                self.assertIn(contact.full_name, contact_details)
                self.assertEqual(f"{count}.", global_index)
        return result


class TestLoPInfo(TestListOfParticipants):
    ORG_TYPE = "GOV"

    def test_doc_symbols(self):
        self.event.lop_doc_symbols = ["UNEP/Ozj/i3o/If/1", "UNEP/Ozj/i3o/If/2"]
        self.event.save()

        doc = self.get_doc()
        text = extract_text_from_docx_headers(doc)
        self.assertIn("UNEP/Ozj/i3o/If/1-UNEP/Ozj/i3o/If/2", text)

        text = extract_text_from_docx(doc)
        self.assertIn("UNEP/Ozj/i3o/If/1", text)
        self.assertIn("UNEP/Ozj/i3o/If/2", text)

    def test_doc_footer(self):
        doc = self.get_doc()
        text = extract_text_from_docx_footers(doc)
        self.assertIn(str(timezone.now().date()), text)

    def test_contact_info(self):
        self.reg1.designation = "Plumber"
        self.reg1.department = "Sanitation Department"
        self.reg1.save()

        self.contact1.is_use_organization_address = False
        self.contact1.first_name = "Luigi"
        self.contact1.last_name = "Mario"
        self.contact1.address = "Rainbow Road"
        self.contact1.postal_code = "1234"
        self.contact1.city = "Toad Town"
        self.contact1.state = "Mushroom Kingdom"
        self.contact1.country = self.country3
        self.contact1.save()

        info = self.check_doc()["Romania"][1][1]

        self.assertEqual(
            info.split("\n"),
            [
                "Mr. Luigi Mario",
                "Plumber",
                "Sanitation Department",
                self.org1.name,
                "Rainbow Road",
                "Toad Town, Mushroom Kingdom, 1234",
                "France",
                "Email: contact@example.com",
            ],
        )

    def test_contact_info_org_address(self):
        self.reg1.designation = "Plumber"
        self.reg1.department = "Sanitation Department"
        self.reg1.save()

        self.contact1.first_name = "Luigi"
        self.contact1.last_name = "Mario"
        self.contact1.is_use_organization_address = True
        self.contact1.save()

        self.org1.address = "Rainbow Road"
        self.org1.postal_code = "1234"
        self.org1.city = "Toad Town"
        self.org1.state = "Mushroom Kingdom"
        self.org1.country = self.country3
        self.org1.save()

        info = self.check_doc()["Romania"][1][1]

        self.assertEqual(
            info.split("\n"),
            [
                "Mr. Luigi Mario",
                "Plumber",
                "Sanitation Department",
                self.org1.name,
                "Rainbow Road",
                "Toad Town, Mushroom Kingdom, 1234",
                "France",
                "Email: contact@example.com",
            ],
        )

    def test_contact_info_missing_reg_data(self):
        self.reg1.organization = None
        self.reg1.save()

        self.contact1.is_use_organization_address = False
        self.contact1.designation = "Plumber"
        self.contact1.department = "Sanitation Department"
        self.contact1.first_name = "Luigi"
        self.contact1.last_name = "Mario"
        self.contact1.address = "Rainbow Road"
        self.contact1.postal_code = "1234"
        self.contact1.city = "Toad Town"
        self.contact1.state = "Mushroom Kingdom"
        self.contact1.country = self.country3
        self.contact1.save()

        info = self.check_doc()["Romania"][1][1]

        self.assertEqual(
            info.split("\n"),
            [
                "Mr. Luigi Mario",
                "Plumber",
                "Sanitation Department",
                self.org1.name,
                "Rainbow Road",
                "Toad Town, Mushroom Kingdom, 1234",
                "France",
                "Email: contact@example.com",
            ],
        )


class TestLoPParties(TestListOfParticipants):
    ORG_TYPE = "GOV"

    def test_party_role_order(self):
        self.check_doc(
            {
                "Romania": [self.contact1, self.contact2],
            }
        )

    def test_party_role_order_override(self):
        self.reg2.sort_order = 1
        self.reg2.save()

        self.check_doc(
            {
                "Romania": [self.contact2, self.contact1],
            }
        )

    def test_party_hide_role(self):
        self.alt_head.hide_in_lop = True
        self.alt_head.save()

    def test_party_same_role_order(self):
        self.reg2.role = self.head
        self.reg2.save()

        self.contact1.last_name = "XXX"
        self.contact1.save()

        self.contact2.last_name = "AAA"
        self.contact2.save()

        self.check_doc(
            {
                "Romania": [self.contact2, self.contact1],
            }
        )

    def test_multiple_parties(self):
        self.org2.government = self.country2
        self.org2.save()

        self.check_doc(
            {
                "Romania": [self.contact1],
                "Spain": [self.contact2],
            }
        )


class TestLoPAss(TestListOfParticipants):
    ORG_TYPE = "ASS-PANEL"

    def test_ass_order(self):
        self.check_doc(
            {
                self.org1.name: [self.contact1],
                self.org2.name: [self.contact2],
            }
        )

    def test_ass_override_sort_order(self):
        self.org1.sort_order = 20
        self.org1.save()

        self.org2.sort_order = 10
        self.org2.save()

        self.check_doc(
            {
                self.org2.name: [self.contact2],
                self.org1.name: [self.contact1],
            }
        )

    def test_ass_same_org_order(self):
        self.reg2.organization = self.org1
        self.reg2.save()

        self.check_doc(
            {
                self.org1.name: [self.contact1, self.contact2],
            }
        )

    def test_ass_same_org_order_same_role(self):
        self.reg2.organization = self.org1
        self.reg2.role = self.head
        self.reg2.save()

        self.check_doc(
            {
                self.org1.name: [self.contact2, self.contact1],
            }
        )

    def test_ass_same_org_role_order_override(self):
        self.reg2.organization = self.org1
        self.reg2.sort_order = 1
        self.reg2.save()

        self.check_doc(
            {
                self.org1.name: [self.contact2, self.contact1],
            }
        )


class TestLoPObs(TestListOfParticipants):
    ORG_TYPE = "OBS"

    def test_obs_order(self):
        self.check_doc(
            {
                self.org1.name: [self.contact1],
                self.org2.name: [self.contact2],
            }
        )

    def test_obs_override_sort_order(self):
        self.org1.sort_order = 20
        self.org1.save()

        self.org2.sort_order = 10
        self.org2.save()

        self.check_doc(
            {
                self.org2.name: [self.contact2],
                self.org1.name: [self.contact1],
            }
        )

    def test_obs_same_org_order(self):
        self.reg2.organization = self.org1
        self.reg2.save()

        self.check_doc(
            {
                self.org1.name: [self.contact1, self.contact2],
            }
        )

    def test_obs_same_org_order_same_role(self):
        self.reg2.organization = self.org1
        self.reg2.role = self.head
        self.reg2.save()

        self.check_doc(
            {
                self.org1.name: [self.contact2, self.contact1],
            }
        )

    def test_obs_same_org_role_order_override(self):
        self.reg2.organization = self.org1
        self.reg2.sort_order = 1
        self.reg2.save()

        self.check_doc(
            {
                self.org1.name: [self.contact2, self.contact1],
            }
        )

    def test_multiple_org_type_order(self):
        self.org2.organization_type = self.biz
        self.org2.save()

        self.check_doc(
            {
                # Alphabetical order Industry -> Observer
                self.org2.name: [self.contact2],
                self.org1.name: [self.contact1],
            }
        )

    def test_multiple_org_type_override_order(self):
        self.org2.organization_type = self.biz
        self.org2.save()

        self.obs.sort_order = 10
        self.obs.save()

        self.biz.sort_order = 20
        self.biz.save()

        self.check_doc(
            {
                self.org1.name: [self.contact1],
                self.org2.name: [self.contact2],
            }
        )


class TestLoPSec(TestListOfParticipants):
    ORG_TYPE = "SECRETARIAT"

    def test_sec_order(self):
        self.check_doc(
            {
                self.org1.name: [self.contact1],
                self.org2.name: [self.contact2],
            }
        )

    def test_sec_override_sort_order(self):
        self.org1.sort_order = 20
        self.org1.save()

        self.org2.sort_order = 10
        self.org2.save()

        self.check_doc(
            {
                self.org2.name: [self.contact2],
                self.org1.name: [self.contact1],
            }
        )

    def test_sec_same_org_order(self):
        self.reg2.organization = self.org1
        self.reg2.save()

        self.check_doc(
            {
                self.org1.name: [self.contact1, self.contact2],
            }
        )

    def test_sec_same_org_order_same_role(self):
        self.reg2.organization = self.org1
        self.reg2.role = self.head
        self.reg2.save()

        self.check_doc(
            {
                self.org1.name: [self.contact2, self.contact1],
            }
        )

    def test_sec_same_org_role_order_override(self):
        self.reg2.organization = self.org1
        self.reg2.sort_order = 1
        self.reg2.save()

        self.check_doc(
            {
                self.org1.name: [self.contact2, self.contact1],
            }
        )
