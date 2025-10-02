import io

import docx.document
from django.test import TestCase
from django.urls import reverse

from api.tests.factories import (
    ContactFactory,
    EventFactory,
    OrganizationFactory,
    RegistrationFactory,
)
from core.models import BaseContact, Country, OrganizationType, Subregion
from events.models import Registration
from events.tests.utils import get_table_data


class TestsPostMeetingStatistics(TestCase):
    fixtures = [
        "initial/organizationtype",
        "initial/region",
        "initial/subregion",
        "initial/country",
        "initial/role",
        "test/user",
    ]

    def setUp(self):
        self.event = EventFactory()

        self.country1 = Country.objects.get(pk="RO")
        self.country2 = Country.objects.get(pk="EG")

        self.gov = OrganizationType.objects.get(acronym="GOV")
        self.ass = OrganizationType.objects.get(acronym="ASS-PANEL")
        self.obs = OrganizationType.objects.get(acronym="OBS")

        self.org1 = OrganizationFactory(
            government=self.country1, organization_type=self.gov
        )
        self.org2 = OrganizationFactory(
            government=self.country2, organization_type=self.gov
        )

        self.contact1 = ContactFactory(
            organization=self.org1,
            gender=BaseContact.GenderChoices.FEMALE,
        )
        self.contact2 = ContactFactory(
            organization=self.org2,
            gender="",
        )

        self.reg1 = RegistrationFactory(
            event=self.event,
            contact=self.contact1,
            organization=self.org1,
            status=Registration.Status.REGISTERED,
        )
        self.reg2 = RegistrationFactory(
            event=self.event,
            contact=self.contact2,
            organization=self.org2,
            status=Registration.Status.REGISTERED,
        )
        self.url = reverse("admin:post_meeting_statistics", args=(self.event.id,))

    def check_doc(
        self,
        acc_contacts=0,
        reg_contacts=2,
        hl_contacts_reg=0,
        hl_contacts_acc=0,
        a2_parties=1,
        a5_parties=1,
        a2_contacts=1,
        a5_contacts=1,
    ):
        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

        f = io.BytesIO(b"".join(resp.streaming_content))
        doc = docx.Document(f)
        result = get_table_data(doc)

        self.assertEqual(
            result["Table 1: Participants by Category and Gender"][-1][1],
            str(acc_contacts + reg_contacts),
            "T1: Total number of participants should be acc + reg",
        )
        self.assertEqual(
            result["Table 1: Participants by Category and Gender"][-1][2],
            str(reg_contacts),
            "T1: Invalid number of registered participants",
        )

        self.assertEqual(
            result["Table 2: A2 Participants by Region and Gender"][-1][1],
            str(a2_parties),
            "T2: invalid number of A2 registered participants",
        )
        self.assertEqual(
            result["Table 2: A2 Participants by Region and Gender"][-1][2],
            str(a2_contacts),
            "T2: invalid number of A2 registered participants",
        )

        self.assertEqual(
            result["Table 3: A5 Participants by Region and Gender"][-1][1],
            str(a5_parties),
            "T3: invalid number of A5 registered parties",
        )
        self.assertEqual(
            result["Table 3: A5 Participants by Region and Gender"][-1][2],
            str(a5_contacts),
            "T3: invalid number of A5 registered parties",
        )

        self.assertEqual(
            result["Table 4: HL"][-1][0],
            f"Total (Registered): {hl_contacts_reg}\nTotal (Accredited): {hl_contacts_acc}",
            "T4: Invalid number of HL participants",
        )

        return result

    def test_empty(self):
        self.reg1.delete()
        self.reg2.delete()

        self.check_doc(
            acc_contacts=0,
            reg_contacts=0,
            hl_contacts_reg=0,
            hl_contacts_acc=0,
            a2_parties=0,
            a5_parties=0,
            a2_contacts=0,
            a5_contacts=0,
        )

    def test_get_data(self):
        self.check_doc()

    def test_t1(self):
        self.org1.organization_type = self.obs
        self.org1.save()

        self.org2.organization_type = self.ass
        self.org2.save()

        result = self.check_doc(
            acc_contacts=0,
            reg_contacts=2,
            hl_contacts_reg=0,
            hl_contacts_acc=0,
            a2_parties=0,
            a5_parties=0,
            a2_contacts=0,
            a5_contacts=0,
        )

        obs_row = result["Table 1: Participants by Category and Gender"][4]
        ass_row = result["Table 1: Participants by Category and Gender"][5]

        self.assertEqual(obs_row[0], "Observers")
        self.assertEqual(obs_row[1], "1")
        self.assertEqual(obs_row[4], "1")

        self.assertEqual(ass_row[0], "Assessment Panels")
        self.assertEqual(ass_row[1], "1")
        self.assertEqual(ass_row[7], "1")

    def test_t2(self):
        result = self.check_doc()
        row = result["Table 2: A2 Participants by Region and Gender"][4]

        self.assertEqual(row[0], "European Union")
        self.assertEqual(row[1], "1")
        self.assertEqual(row[2], "1")
        self.assertEqual(row[4], "1")

    def test_t3(self):
        result = self.check_doc()
        row = result["Table 3: A5 Participants by Region and Gender"][3]

        self.assertEqual(row[0], "Anglophone Africa")
        self.assertEqual(row[1], "1")
        self.assertEqual(row[2], "1")
        self.assertEqual(row[7], "1")

    def test_t4(self):
        self.contact1.title = BaseContact.Title.HE_MR
        self.contact1.save()

        self.contact2.title = BaseContact.Title.HON_MS
        self.contact2.save()

        result = self.check_doc(hl_contacts_reg=2, hl_contacts_acc=0)
        self.assertEqual(
            result["Table 4: HL"][2],
            [
                self.country2.name,
                self.org2.name,
                self.contact2.designation,
                self.contact2.full_name,
                "Registered",
            ],
        )
        self.assertEqual(
            result["Table 4: HL"][3],
            [
                self.country1.name,
                self.org1.name,
                self.contact1.designation,
                self.contact1.full_name,
                "Registered",
            ],
        )

    def test_subregion_sort_order(self):
        Subregion.objects.filter(code="EUN").update(sort_order=20)
        Subregion.objects.filter(code="AFE").update(sort_order=20)
        result = self.check_doc()

        row = result["Table 2: A2 Participants by Region and Gender"][-2]
        self.assertEqual(row[:2], ["European Union", "1"])

        row = result["Table 3: A5 Participants by Region and Gender"][-2]
        self.assertEqual(row[:2], ["Anglophone Africa", "1"])
