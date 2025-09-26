import io
from datetime import datetime, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook

from api.tests.factories import (
    ContactFactory,
    CountryFactory,
    DSAFactory,
    EventFactory,
    OrganizationFactory,
    RegistrationFactory,
)
from core.models import OrganizationType
from events.models import Registration, RegistrationTag


class TestDSAReport(TestCase):
    fixtures = [
        "initial/organizationtype",
        "initial/registrationtag",
        "initial/role",
        "test/user",
    ]

    def setUp(self):
        self.maxDiff = None
        self.event = EventFactory()

        self.is_funded = RegistrationTag.objects.get(name="Is funded")

        self.country1 = CountryFactory()
        self.country2 = CountryFactory()

        self.gov = OrganizationType.objects.get(acronym="GOV")
        self.ass = OrganizationType.objects.get(acronym="ASS-PANEL")

        self.org1 = OrganizationFactory(
            government=self.country1, organization_type=self.gov
        )
        self.org2 = OrganizationFactory(
            country=self.country2, organization_type=self.ass
        )

        self.contact1 = ContactFactory(organization=self.org1)
        self.contact2 = ContactFactory(organization=self.org2)

        self.reg1 = RegistrationFactory(
            event=self.event,
            contact=self.contact1,
            organization=self.org1,
            status=Registration.Status.REGISTERED,
        )
        self.reg1.tags.add(self.is_funded)
        self.reg2 = RegistrationFactory(
            event=self.event,
            contact=self.contact2,
            organization=self.org2,
            status=Registration.Status.REGISTERED,
        )
        self.reg2.tags.add(self.is_funded)

        self.today = timezone.now().date()
        self.date1 = datetime.combine(self.today, datetime.min.time())
        self.date2 = datetime.combine(
            self.date1 + timedelta(days=7), datetime.min.time()
        )

        self.dsa1 = DSAFactory(
            registration=self.reg1, arrival_date=self.date1, departure_date=self.date2
        )
        self.dsa2 = DSAFactory(
            registration=self.reg2, arrival_date=self.date1, departure_date=self.date2
        )

    def check_report(self, expected=None, max_col=10):
        url = reverse("admin:dsa", args=(self.event.id,))
        self.client.login(email="admin@example.com", password="admin")
        resp = self.client.get(url)
        f = io.BytesIO(b"".join(resp.streaming_content))
        wb = load_workbook(f, read_only=True, data_only=True)
        ws = wb.active

        result = []
        for row in ws.iter_rows(min_row=7):
            row_result = []
            for cell in row[1:max_col]:
                row_result.append(cell.value)

            result.append(row_result)

        if expected:
            self.assertEqual(result[:-1], expected)
        return result[:-1]

    def check_contacts(self, expected_contacts):
        result = self.check_report()

        self.assertEqual(len(result), len(expected_contacts))
        for row, contact in zip(result, expected_contacts, strict=False):
            self.assertEqual(row[5], contact.last_name)

    def test_dsa_report(self):
        self.check_report(
            [
                [
                    1,
                    self.country1.name,
                    str(self.dsa1.umoja_travel),
                    str(self.dsa1.bp),
                    str(self.contact1.title),
                    self.contact1.last_name,
                    self.contact1.first_name,
                    self.date1,
                    self.date2,
                ],
                [
                    2,
                    self.country2.name,
                    str(self.dsa2.umoja_travel),
                    str(self.dsa2.bp),
                    str(self.contact2.title),
                    self.contact2.last_name,
                    self.contact2.first_name,
                    self.date1,
                    self.date2,
                ],
            ]
        )

    def test_dsa_missing(self):
        self.dsa1.delete()
        self.check_contacts([self.contact2])

    def test_not_funded(self):
        self.reg1.tags.remove(self.is_funded)
        self.check_contacts([self.contact2])

    def test_no_country(self):
        self.org1.government = None
        self.org1.save()
        self.check_contacts([self.contact1, self.contact2])

    def test_no_dates(self):
        self.dsa1.arrival_date = None
        self.dsa1.departure_date = None
        self.dsa1.save()
        self.check_contacts([self.contact1, self.contact2])
