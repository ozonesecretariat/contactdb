from datetime import datetime
from unittest.mock import patch
from django.test import TestCase
from django.utils.timezone import make_naive
from events.models import Event, LoadEventsFromKronosTask


class TestImportEvents(TestCase):
    fixtures = [
        "initial/country",
        # "initial/organizationtype",
        # "initial/registrationrole",
        # "initial/registrationstatus",
        # "initial/registrationtag",
    ]

    def setUp(self):
        self.fake_item = {
            "code": "QQ:ASAS",
            "dates": "1-10 July 2010",
            "endDate": "2010-07-10T00:00:00Z",
            "eventId": "abcdefg123456789",
            "isOpenForRegistration": False,
            "startDate": "2010-07-1T00:00:00Z",
            "title": " \t Quantum Quest: A Science Adventure Symposium  ",
            "venueCity": "Kathmandu",
            "venueCountry": "np",
        }

        self.mock_data = [self.fake_item]
        self.mock_client = patch("events.parsers.KronosClient").start()
        self.mock_client.return_value.get_meetings.side_effect = (
            lambda *args: self.mock_data
        )

    def tearDown(self):
        patch.stopall()

    def test_sync_events(self):
        LoadEventsFromKronosTask.objects.create().run(is_async=False)

        self.assertEqual(Event.objects.count(), 1)
        event = Event.objects.first()

        self.assertEqual(event.event_id, "abcdefg123456789")
        self.assertEqual(make_naive(event.start_date), datetime(2010, 7, 1))
        self.assertEqual(make_naive(event.end_date), datetime(2010, 7, 10))
        self.assertEqual(event.dates, "1-10 July 2010")
        self.assertEqual(event.title, "Quantum Quest: A Science Adventure Symposium")
        self.assertEqual(event.venue_city, "Kathmandu")
        self.assertEqual(event.venue_country.code, "NP")

    def test_update_existing(self):
        LoadEventsFromKronosTask.objects.create().run(is_async=False)
        self.assertEqual(Event.objects.count(), 1)
        event = Event.objects.first()

        self.fake_item["title"] = "Quantum Quest: A Science Adventure Convention"
        self.fake_item["venueCountry"] = "zw"
        self.fake_item["venueCity"] = "Harare"

        LoadEventsFromKronosTask.objects.create().run(is_async=False)
        self.assertEqual(Event.objects.count(), 1)
        event.refresh_from_db()

        self.assertEqual(event.title, "Quantum Quest: A Science Adventure Convention")
        self.assertEqual(event.venue_country.code, "ZW")
        self.assertEqual(event.venue_city, "Harare")
