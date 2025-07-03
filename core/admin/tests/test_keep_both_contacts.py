from copy import deepcopy
from unittest.mock import patch

from django.urls import reverse

from api.tests.base import BaseAPITestCase
from core.models import (
    Country,
    Organization,
    OrganizationType,
)
from events.models import Event


class TestKeepBothContacts(BaseAPITestCase):
    url = "/admin/core/resolveconflict/"
    fixtures = [
        "initial/role",
        "test/user",
        "initial/region",
        "initial/subregion",
        "initial/country",
        "initial/organizationtype",
        "initial/registrationrole",
        "initial/registrationtag",
    ]

    def setUp(self):
        self.event = Event.objects.create(
            event_id="eventid",
            title="Quantum Quest: A Science Adventure Symposium",
            code="POM-2023",
            start_date="2023-01-01T00:00:00Z",
            end_date="2023-01-05T00:00:00Z",
            dates="1 - 5 January 2023",
        )

        self.organization = Organization.objects.create(
            name="Literary Society",
            organization_id="orgid",
            acronym="LS",
            country=Country.objects.get(code="GB"),
            government=Country.objects.get(code="GB"),
            organization_type=OrganizationType.objects.get(acronym="GOV"),
        )

        self.mock_client = patch("core.parsers.KronosClient").start()
        self.mock_client.return_value.get_contact_data.side_effect = (
            lambda *args: deepcopy(self.fake_contact)
        )

        self.mock_client.return_value.get_registrations_data.side_effect = (
            lambda *args: deepcopy(self.fake_registration)
        )

    def tearDown(self):
        patch.stopall()

    def test_keep_both_local_contacts(self):
        """
        Test that keeping both contacts works with local contacts
        (contacts that were not imported from Kronos).
        """
        self.login_admin()
        data = {
            "action": "keep_both_contacts",
            "select_across": "0",
            "index": "0",
            "_selected_action": "1",
        }

        url = reverse("admin:core_resolveconflict_changelist")

        response = self.client.post(
            path=url,
            data=data,
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        # TODO
