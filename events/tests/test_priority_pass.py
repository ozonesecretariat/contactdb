from django.test import TestCase

from api.tests.factories import (
    ContactFactory,
    EventFactory,
    PriorityPassFactory,
    RegistrationFactory,
)
from events.models import Registration


class TestPriorityPass(TestCase):
    def setUp(self):
        self.contact = ContactFactory()
        self.event1 = EventFactory(start_date="2025-11-01", end_date="2025-11-01")
        self.event2 = EventFactory(start_date="2025-12-01", end_date="2025-12-01")
        self.event3 = EventFactory(start_date="2025-12-01", end_date="2026-01-01")

        self.priority_pass = PriorityPassFactory()

        self.reg1 = RegistrationFactory(
            contact=self.contact,
            event=self.event1,
            status=Registration.Status.REGISTERED,
            priority_pass=self.priority_pass,
        )
        self.reg2 = RegistrationFactory(
            contact=self.contact,
            event=self.event2,
            status=Registration.Status.REGISTERED,
            priority_pass=self.priority_pass,
        )
        self.reg3 = RegistrationFactory(
            contact=self.contact,
            event=self.event3,
            status=Registration.Status.REGISTERED,
            priority_pass=self.priority_pass,
        )

    def test_different_years(self):
        self.assertEqual(
            self.priority_pass.valid_date_range, "1 Nov 2025 to 1 Jan 2026"
        )

    def test_gap_revoke_years(self):
        self.reg2.status = Registration.Status.REVOKED
        self.reg2.save()

        self.assertEqual(
            self.priority_pass.valid_date_range, "1 Nov 2025 to 1 Jan 2026"
        )

    def test_same_year(self):
        self.event3.end_date = "2025-12-31"
        self.event3.save()

        self.assertEqual(self.priority_pass.valid_date_range, "1 Nov - 31 Dec 2025")

    def test_same_month(self):
        self.event1.start_date = "2025-12-03"
        self.event1.end_date = "2025-12-05"
        self.event1.save()
        self.event3.end_date = "2025-12-31"
        self.event3.save()

        self.assertEqual(self.priority_pass.valid_date_range, "1-31 Dec 2025")

    def test_same_day(self):
        self.reg2.status = Registration.Status.REVOKED
        self.reg2.save()
        self.reg3.status = Registration.Status.REVOKED
        self.reg3.save()

        self.assertEqual(self.priority_pass.valid_date_range, "1 Nov 2025")

    def test_no_day(self):
        self.reg1.status = Registration.Status.REVOKED
        self.reg1.save()
        self.reg2.status = Registration.Status.REVOKED
        self.reg2.save()
        self.reg3.status = Registration.Status.REVOKED
        self.reg3.save()

        self.assertEqual(self.priority_pass.valid_date_range, "")
