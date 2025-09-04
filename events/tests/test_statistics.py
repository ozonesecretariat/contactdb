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
from core.models import Country, OrganizationType
from events.models import Registration
from events.tests.utils import get_table_data


class TestsPreMeetingStatistics(TestCase):
    fixtures = [
        "initial/organizationtype",
        "initial/region",
        "initial/subregion",
        "initial/country",
        "initial/role",
        "test/user",
    ]

    def setUp(self):
        self.country = Country.objects.get(pk="RO")
        self.org_type = OrganizationType.objects.get(acronym="GOV")
        self.org = OrganizationFactory(
            organization_type=self.org_type, government=self.country
        )
        self.contact = ContactFactory(organization=self.org)
        self.registration = RegistrationFactory(
            status=Registration.Status.ACCREDITED,
            organization=self.org,
            contact=self.contact,
        )
        self.event = self.registration.event
        self.url = reverse("admin:pre_meeting_statistics", args=(self.event.id,))

        self.no_data_event = EventFactory()
        self.url_no_data = reverse(
            "admin:pre_meeting_statistics", args=(self.no_data_event.id,)
        )

    def parse_doc(self, resp, pax=0, gov=0, a5=0, a2=0):
        f = io.BytesIO(b"".join(resp.streaming_content))
        doc = docx.Document(f)
        result = list(get_table_data(doc).values())
        self.assertEqual(result[0][-1], ["Total", str(pax)])
        self.assertEqual(result[1][-1], ["Total", str(gov), "", ""])
        self.assertEqual(
            result[2][-1],
            ["Total", "155", str(a5), str(155 - a5), str(a5), "", "", ""],
        )
        self.assertEqual(result[3][-1], ["Total", "43", str(a2), str(43 - a2), str(a2)])

        return result

    def test_no_data(self):
        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(self.url_no_data)
        self.assertEqual(resp.status_code, 200)

        self.parse_doc(resp, pax=0, gov=0, a5=0, a2=0)

    def test_non_staff(self):
        self.client.login(email="test-non-staff@example.com", password="test-non-staff")
        resp = self.client.get(self.url_no_data)
        self.assertEqual(resp.status_code, 302)

    def test_get_data(self):
        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

        result = self.parse_doc(resp, pax=1, gov=1, a5=0, a2=1)

        self.assertEqual(result[0][7], ["Parties", "1"])
        self.assertEqual(result[1][2], ["A2 Parties", "1", "100.00%", "2.33%"])
        self.assertEqual(result[3][3], ["European Union", "28", "1", "27", "1"])

    def test_no_org_type(self):
        self.org.organization_type = None
        self.org.save()

        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

        result = self.parse_doc(resp, pax=1, gov=0, a5=0, a2=0)
        self.assertEqual(result[0][-2], ["Unknown", "1"])

    def test_no_org(self):
        self.registration.organization = None
        self.registration.save()
        self.contact.organization = None
        self.contact.save()

        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

        result = self.parse_doc(resp, pax=1, gov=0, a5=0, a2=0)
        self.assertEqual(result[0][-2], ["Unknown", "1"])

    def test_no_org_registration(self):
        self.registration.organization = None
        self.registration.save()

        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

        result = self.parse_doc(resp, pax=1, gov=1, a5=0, a2=1)

        self.assertEqual(result[0][7], ["Parties", "1"])
        self.assertEqual(result[1][2], ["A2 Parties", "1", "100.00%", "2.33%"])
        self.assertEqual(result[3][3], ["European Union", "28", "1", "27", "1"])

    def test_no_org_contact(self):
        self.contact.organization = None
        self.contact.save()

        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

        result = self.parse_doc(resp, pax=1, gov=1, a5=0, a2=1)

        self.assertEqual(result[0][7], ["Parties", "1"])
        self.assertEqual(result[1][2], ["A2 Parties", "1", "100.00%", "2.33%"])
        self.assertEqual(result[3][3], ["European Union", "28", "1", "27", "1"])

    def test_no_gov(self):
        self.org.government = None
        self.org.save()

        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

        self.parse_doc(resp, pax=1, gov=0, a5=0, a2=0)

    def test_no_gov_org_type(self):
        self.org.organization_type = OrganizationType.objects.get(acronym="OTHER")
        self.org.save()

        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

        self.parse_doc(resp, pax=1, gov=0, a5=0, a2=0)
