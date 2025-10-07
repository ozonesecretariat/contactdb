from datetime import datetime
from unittest.mock import patch

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


class TestPriorityPassTimezones(TestCase):
    def setUp(self):
        self.contact = ContactFactory()
        self.event = EventFactory(
            start_date="2025-12-01 00:00:00",
            end_date="2026-01-01 00:00:00",
            timezone="Europe/Bucharest",
        )
        self.priority_pass = PriorityPassFactory()
        self.reg = RegistrationFactory(
            event=self.event,
            contact=self.contact,
            status=Registration.Status.REGISTERED,
            priority_pass=self.priority_pass,
        )

    def check_valid(self, mock_date, expected):
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = datetime.fromisoformat(mock_date)
            self.assertEqual(self.priority_pass.is_currently_valid, expected)

    def test_is_currently_valid(self):
        # 10 minutes too early
        self.check_valid("2025-11-30 21:50:00+00:00", False)
        # Right at the event start
        self.check_valid("2025-11-30 22:00:00+00:00", True)
        # Right at the event end
        self.check_valid("2025-12-31 22:00:00+00:00", True)
        # 10 minutes too late
        self.check_valid("2025-12-31 22:10:10+00:00", False)

    def test_not_registered(self):
        self.reg.status = Registration.Status.REVOKED
        self.reg.save()

        self.check_valid("2025-12-02 00:00:00+00:00", False)
